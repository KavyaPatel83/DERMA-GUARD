# Understanding DERMA-GUARD results

## What the system does
DERMA-GUARD is a research system that combines a lesion photograph, patient details such as age, body site, size and symptoms, and a free-text description. Seven model configurations, labelled A to G, cover every combination of these three inputs. The system picks the model that matches the inputs you supplied and also asks all other applicable models to vote. Measured on cases the models never trained on, image-based configurations reach roughly 61 to 65 percent accuracy and the metadata-only configuration roughly 78 percent, so results are always shown with calibrated confidence and a prediction set.

## Confidence
Confidence is the model's probability for its top prediction. A high number does not guarantee correctness. It is a statement about the model's belief, not the real-world chance of being right, and it can be overconfident on unusual cases or poor photographs.

## Conformal prediction set
Instead of one label, the system also reports a set of plausible diagnoses calibrated on held-out cases to cover the true answer about 90 percent of the time. Because the models are only moderately accurate, these sets are often large, which is the system being honest about its uncertainty. A set with one class means the case looks clear to the model. A set with several classes means real ambiguity, and a clinician should look at it.

## Evidence quality, reliability and sufficiency
Each input is scored for quality, such as photograph sharpness or how many patient fields are filled, and for reliability, such as how stable and low-entropy the prediction is. These are combined into a sufficiency score. Below 0.30 the system declines to decide, between 0.30 and 0.50 it asks for more evidence, and above 0.50 it proceeds.

## Four decision levels
ACCEPT means evidence is sufficient, models agree and confidence is high. ARBITRATE means models broadly agree but confidence is moderate, so a clinician should confirm. ACQUIRE means more or better input is needed, for example a clearer photo. ESCALATE means the case is too uncertain or too risky for automated triage, or a malignant class appears in the plausible set while the top prediction is benign, and a specialist should review it.

## Why the assistant might say it needs more information
A single blurry photograph, a very short description, or missing patient details lower the evidence score. Adding a clear close-up photo, the lesion size, and how it has changed over time improves reliability.

## Limitations
The system was trained and tested on one public dataset, PAD-UFES-20, collected in Brazil. The free-text modality is synthetic, generated from structured fields. Melanoma is rare in the data, so its metrics are unstable. The system is a research prototype and is not a medical device. It must never be used as the only basis for any clinical decision.
