# ONION_SURE 🧅

A comprehensive open-source image dataset and quality assurance resource for onion crop analysis, featuring classified images of onion bulbs and leaves in healthy and unhealthy states.

---

## 📊 Dataset Overview

- **Total Images:** 24,000 images (`.jpg` format)
- **Total Size:** ~2.34 GB
- **Categories Covered:** Bulb and Leaves (Healthy vs. Unhealthy)

### Distribution Breakdown

| Part | Condition | Count | Description |
| :--- | :--- | :--- | :--- |
| **Bulb** | Healthy | 12,367 | High-quality, disease-free onion bulbs |
| **Bulb** | Unhealthy | 5,461 | Bulbs exhibiting decay, blemishes, or damage |
| **Leaves** | Healthy | 3,104 | Fresh, vibrant, disease-free onion foliage |
| **Leaves** | Unhealthy | 3,068 | Leaves with blight, discoloration, or pest damage |
| **Total** | | **24,000** | |

---

## 📁 Repository Directory Structure

```text
ONION_SURE/
├── README.md
├── .gitignore
└── Red and White Onion Dataset/
    └── New Onion/
        ├── Bulb/
        │   ├── Healthy/      # 12,367 images
        │   └── Unhealthy/    # 5,461 images
        └── Leaves/
            ├── Healthy/      # 3,104 images
            └── Unhealthy/    # 3,068 images
```

---

## 🚀 Potential Use Cases

- **Agricultural Computer Vision:** Training Convolutional Neural Networks (CNNs) and Vision Transformers (ViTs) for plant pathology.
- **Automated Sorting & Grading:** Developing conveyor belt inspection systems for post-harvest onion sorting.
- **Early Disease Detection:** Deploying edge AI models (YOLO, MobileNet, EfficientNet) to assist farmers in real-time crop monitoring.
- **Transfer Learning & Benchmarking:** Serving as a baseline benchmark for horticultural image classification datasets.

---

## 🛠️ Usage Example (Python & PyTorch)

```python
import torchvision.transforms as transforms
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader

# Preprocessing transforms
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Load Bulb dataset
bulb_dataset = ImageFolder(root='Red and White Onion Dataset/New Onion/Bulb', transform=transform)
bulb_loader = DataLoader(bulb_dataset, batch_size=32, shuffle=True)

print(f"Classes: {bulb_dataset.classes}")
print(f"Total samples: {len(bulb_dataset)}")
```

---

## 🤝 Contribution & License

Contributions, model benchmarks, and improvements are welcome! Feel free to open an issue or submit a pull request.