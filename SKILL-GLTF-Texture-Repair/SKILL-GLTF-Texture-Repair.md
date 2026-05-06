# Skill: GLTF 贴图引用修复标准流程

## 1. 问题诊断清单

在修复前，按以下顺序诊断 glTF 模型的贴图问题：

- [ ] **检查 `images` 段**：`grep -o '"images"' model.gltf`，若不存在说明贴图引用完全丢失
- [ ] **检查 `textures` 段**：确认 texture 对象是否存在
- [ ] **检查 `samplers` 段**：确认采样器是否存在
- [ ] **检查 material 的贴图引用**：确认 `baseColorTexture`/`metallicRoughnessTexture`/`normalTexture`/`emissiveTexture`/`occlusionTexture` 是否存在
- [ ] **检查 mesh 与 material 的对应关系**：一个 material 是否被错误分配给了本应使用不同贴图的多个 mesh

## 2. 贴图文件命名规范（建议）

为保证自动匹配成功率，贴图文件应遵循以下命名约定：

```
{前缀}_{编号}_{类型}.jpeg
```

| 贴图类型 | 前缀 | 后缀关键字 | glTF 属性 |
|---------|------|-----------|-----------|
| BaseColor | `RGB` | `BaseColor` | `baseColorTexture` |
| Metallic | `R` | `Metallic` | 合并到 `metallicRoughnessTexture` (B通道) |
| Roughness | `R` | `Roughness` | 合并到 `metallicRoughnessTexture` (G通道) |
| Normal | `N` | `Normal` | `normalTexture` |
| Emissive | `RGB` | `Emissive` | `emissiveTexture` |
| AO | `R` | `AO` | `occlusionTexture` |
| Opacity | `R` | `Opacity` | 用于 `alphaMode=BLEND` |

**示例**：
```
RGB_01_MinEn_BaseColor.jpeg
R_01_MinEn_Metallic.jpeg
R_01_MinEn_Roughness.jpeg
N_01_MinEn_DirectX_Normal.jpeg
```

## 3. 标准修复流程

### Step 1: 环境准备
```bash
pip install Pillow
```

### Step 2: 运行自动修复脚本
```bash
python gltf_texture_repair.py <model.gltf>
```

### Step 3: 手动验证（若自动修复不满足）

#### 3.1 检查合并贴图
脚本会自动生成 `merged_{编号}_MetallicRoughness.jpeg`。用图像查看器确认：
- 绿色通道 = Roughness
- 蓝色通道 = Metallic

#### 3.2 验证 mesh-material 映射
```python
import json
with open('model.gltf') as f:
    data = json.load(f)

for i, mesh in enumerate(data['meshes']):
    mat_idx = mesh['primitives'][0].get('material')
    mat_name = data['materials'][mat_idx]['name'] if mat_idx is not None else 'None'
    print(f"Mesh {i}: {mesh['name']} -> Material {mat_idx} ({mat_name})")
```

#### 3.3 验证贴图文件存在性
```python
import os
for img in data.get('images', []):
    if not os.path.exists(img['uri']):
        print(f"缺失贴图: {img['uri']}")
```

### Step 4: 3D 查看器最终验证
使用以下工具打开修复后的 glTF 文件：
- **Windows**: 3D Viewer (系统自带)
- **Web**: https://gltf-viewer.donmccurdy.com/
- **Blender**: 导入 glTF 检查贴图是否正确加载

## 4. 常见问题与解决方案

### Q1: Metallic 和 Roughness 是分开的文件，如何合并？
**A**: 使用 Pillow 合并为 glTF 标准格式：
```python
from PIL import Image
met = Image.open('metallic.jpg').convert('L')
rough = Image.open('roughness.jpg').convert('L')
r = Image.new('L', met.size, 0)
merged = Image.merge('RGB', [r, rough, met])
merged.save('merged_MR.jpg', quality=95)
```

### Q2: 透明材质不显示透明效果？
**A**: 确保 material 设置了 `"alphaMode": "BLEND"`，且 BaseColor 贴图或 `baseColorFactor` 包含 alpha < 1.0。

### Q3: Normal 贴图方向错误（凹凸反转）？
**A**: 检查贴图文件名：
- `DirectX_Normal`：Y轴向下，大部分渲染器需要翻转绿色通道
- `OpenGL_Normal`：Y轴向上，glTF 标准格式
若使用 DirectX Normal，可在 material 中设置 `"normalTexture": {"scale": -1}` 尝试修复。

### Q4: mesh 名称没有编号信息，如何匹配贴图？
**A**: 修改 [`gltf_texture_repair.py`](gltf_texture_repair.py) 中的 `extract_material_id()` 方法，根据实际命名规则调整正则表达式。

## 5. 输出文件清单

修复完成后，目录中应包含：

| 文件 | 说明 |
|------|------|
| `model.gltf` | 修复后的主文件（原文件自动备份为 `.gltf.bak`） |
| `merged_{ID}_MetallicRoughness.jpeg` | 自动合并的 Metallic/Roughness 贴图 |
| 原始贴图文件 | 保持不变，继续被引用 |

## 6. glTF 贴图结构速查

```json
{
  "samplers": [{ "magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497 }],
  "images": [{ "uri": "RGB_01_BaseColor.jpeg" }],
  "textures": [{ "sampler": 0, "source": 0 }],
  "materials": [{
    "pbrMetallicRoughness": {
      "baseColorTexture": { "index": 0 },
      "metallicRoughnessTexture": { "index": 1 },
      "metallicFactor": 1.0,
      "roughnessFactor": 1.0
    },
    "normalTexture": { "index": 2 },
    "emissiveTexture": { "index": 3 },
    "occlusionTexture": { "index": 4 },
    "alphaMode": "OPAQUE"
  }]
}
```

---
*Skill Version: 1.0 | 配套脚本: [`gltf_texture_repair.py`](gltf_texture_repair.py)*
