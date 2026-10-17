import torchvision.transforms as transforms

def get_train_transforms(image_size: int = 224) -> transforms.Compose:
    """Training augmentations:
    RandomResizedCrop(224, scale=(0.8, 1.0))
    RandomHorizontalFlip(0.5)
    ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1, hue=0.05)
    RandomRotation(15)
    ToTensor()
    Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
    """
    return transforms.Compose([
        transforms.RandomResizedCrop(image_size, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1, hue=0.05),
        transforms.RandomRotation(15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                             std=[0.229, 0.224, 0.225])
    ])

def get_eval_transforms(image_size: int = 224) -> transforms.Compose:
    """Eval transforms:
    Resize(256)
    CenterCrop(224)
    ToTensor()
    Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
    """
    return transforms.Compose([
        transforms.Resize(int(image_size * 256 / 224)),
        transforms.CenterCrop(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                             std=[0.229, 0.224, 0.225])
    ])

if __name__ == "__main__":
    pass
