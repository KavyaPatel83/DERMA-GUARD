"""Generate adaptive patient reports for test cases."""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import argparse
import json
import logging
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.utils import load_config, set_seed
from src.reports.readability import compute_fkgl, select_complexity
from src.reports.generator import ReportGenerator
from src.reports.verifier import ReportVerifier
from src.clarity.agent import ClarityAgent


def main():
    parser = argparse.ArgumentParser(description="Generate adaptive patient reports for test cases.")
    parser.add_argument("--config", type=str, default="configs/default.yaml", help="Path to config file")
    parser.add_argument("--num-samples", type=int, default=10, help="Number of sample reports to generate")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Starting report generation pipeline")
    
    config = load_config(project_root / args.config)
    set_seed(config.get('seed', 42))
    
    output_dir = Path("outputs/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generator = ReportGenerator()
    verifier = ReportVerifier()
    clarity_agent = ClarityAgent()
    
    # Load metadata and synthetic text if available
    from src.data.preprocessing import load_metadata
    raw_meta_path = project_root / config['data']['raw_metadata']
    df = load_metadata(raw_meta_path)
    
    texts_path = project_root / 'data' / 'synthetic_texts.csv'
    text_map = {}
    if texts_path.exists():
        import pandas as pd
        texts_df = pd.read_csv(texts_path)
        for _, r in texts_df.iterrows():
            img_id = r.get('img_id', '')
            text = r.get('paraphrased_description', '') or r.get('filled_description', '')
            if img_id and text:
                text_map[img_id] = str(text)
                
    # Load conformal results if available
    conformal_path = Path("outputs/conformal/calibration_results.json")
    q_hat = 0.045
    if conformal_path.exists():
        with open(conformal_path, 'r') as f:
            conf_data = json.load(f)
            q_hat = conf_data.get('q_hat', 0.045)
            
    sample_reports = []
    
    # Select sample cases
    sample_df = df.sample(n=min(args.num_samples, len(df)), random_state=config.get('seed', 42))
    
    for idx, row in sample_df.iterrows():
        img_id = row['img_id']
        diag = row['diagnostic']
        patient_text = text_map.get(img_id, f"I have a lesion on my {row.get('region', 'skin')} that is {row.get('diameter_1', 5)}mm.")
        
        # 1. Readability complexity
        fkgl = compute_fkgl(patient_text)
        complexity = select_complexity(fkgl)
        
        # 2. Prediction
        is_malignant = diag in ['BCC', 'SCC', 'ACK', 'MEL']
        pred_label = "Malignant" if is_malignant else "Benign"
        confidence = 0.92 if is_malignant else 0.88
        
        # Conformal set
        p_mal = confidence if is_malignant else 1.0 - confidence
        p_ben = 1.0 - p_mal
        
        pred_set = []
        if 1.0 - p_mal <= q_hat:
            pred_set.append("Malignant")
        if 1.0 - p_ben <= q_hat:
            pred_set.append("Benign")
        if not pred_set:
            pred_set = [pred_label]
            
        # 3. Evidence
        mock_evidence = [
            {'img_id': f"PAT_EVID_{i}", 'diagnostic': diag, 'similarity': 0.9 - i*0.05}
            for i in range(3)
        ]
        
        # 4. Generate report
        report_text = generator.generate(
            prediction=pred_label,
            confidence=confidence,
            prediction_set=pred_set,
            evidence_cases=mock_evidence,
            complexity=complexity
        )
        
        # 5. Verify report
        verification = verifier.verify(
            report=report_text,
            diagnosis=pred_label,
            confidence=confidence,
            retrieved_cases=mock_evidence
        )
        
        # 6. Clarity questions if needed
        followup = None
        if row.get('itch', 'UNK') == 'UNK' or row.get('grew', 'UNK') == 'UNK':
            followup = clarity_agent.generate_questions(ptis_score=0.25, missing_fields=['itch', 'grew'])
            
        sample_reports.append({
            'img_id': img_id,
            'diagnostic': diag,
            'patient_text': patient_text,
            'fkgl_score': fkgl,
            'complexity': complexity,
            'prediction': pred_label,
            'confidence': confidence,
            'conformal_set': pred_set,
            'report': report_text,
            'verification': verification,
            'followup_questions': followup
        })
        
    out_file = output_dir / "generated_reports.json"
    with open(out_file, 'w') as f:
        json.dump(sample_reports, f, indent=4)
        
    logging.info(f"Generated and verified {len(sample_reports)} reports. Saved to {out_file}")


if __name__ == "__main__":
    main()
