#!/usr/bin/env python3
"""
GLTF Texture Repair Tool
========================
自动修复缺失贴图引用的 glTF 模型。根据 mesh 名称和目录中的贴图文件，
重建 material、image、texture、sampler 引用，并合并分离的 Metallic/Roughness 贴图。

用法:
    python gltf_texture_repair.py <gltf_file>

要求:
    - 贴图文件与 gltf 文件在同一目录
    - 贴图文件名需包含可识别的编号/类别标识
    - 需要 Pillow (PIL) 库: pip install Pillow
"""

import json
import os
import re
import sys
import copy
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("错误: 需要 Pillow 库。请运行: pip install Pillow")
    sys.exit(1)


class GltfTextureRepair:
    def __init__(self, gltf_path: str):
        self.gltf_path = Path(gltf_path).resolve()
        self.work_dir = self.gltf_path.parent
        self.data = None
        self.texture_files = []
        self.merged_textures = {}
        
        # 贴图类型匹配规则 (prefix, suffix) -> gltf property
        self.texture_rules = {
            ('RGB', 'BaseColor'): 'baseColor',
            ('R', 'Metallic'): 'metallic',
            ('R', 'Roughness'): 'roughness',
            ('N', 'Normal'): 'normal',
            ('RGB', 'Emissive'): 'emissive',
            ('R', 'Opacity'): 'opacity',
        }
        
    def load(self):
        """加载 gltf 文件"""
        print(f"加载: {self.gltf_path}")
        with open(self.gltf_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.texture_files = [
            f for f in os.listdir(self.work_dir)
            if f.lower().endswith(('.jpeg', '.jpg', '.png'))
        ]
        print(f"发现 {len(self.texture_files)} 个贴图文件")
        
    def extract_material_id(self, mesh_name: str) -> str:
        """从 mesh 名称提取材质编号"""
        # 自定义规则区 —— 根据实际项目调整正则
        if 'Smoke' in mesh_name:
            return 'Smoke'
        if 'Water' in mesh_name:
            return 'Water'
        match = re.search(r'_(\d+)_(?:MinEn|Min_)', mesh_name)
        if match:
            return match.group(1)
        # 通用回退：提取最后一个下划线前的数字
        match = re.search(r'_(\d+)(?:_[^_]+)?_\d+$', mesh_name)
        if match:
            return match.group(1)
        return None
        
    def is_opacity_mesh(self, mesh_name: str) -> bool:
        """判断 mesh 是否为透明材质"""
        return 'Opacity' in mesh_name or 'Transparent' in mesh_name
        
    def find_texture(self, prefix: str, material_id: str, suffix: str) -> str:
        """在目录中查找匹配前缀+编号+后缀的贴图文件"""
        if material_id in ('Smoke', None):
            return None
            
        # 构建正则: 前缀_编号_..._后缀.扩展名
        if material_id in ('Water', 'Water_1'):
            pattern = re.compile(
                re.escape(prefix) + r'_.*?' + re.escape(material_id) + 
                r'.*?_' + re.escape(suffix) + r'\.(?:jpeg|jpg|png)',
                re.IGNORECASE
            )
        else:
            pattern = re.compile(
                re.escape(prefix) + r'_' + re.escape(material_id) + 
                r'_.*?' + re.escape(suffix) + r'\.(?:jpeg|jpg|png)',
                re.IGNORECASE
            )
            
        for f in self.texture_files:
            if pattern.search(f):
                return f
        return None
        
    def get_merged_metallic_roughness(self, material_id: str) -> str:
        """获取或生成合并的 MetallicRoughness 贴图"""
        if material_id in self.merged_textures:
            return self.merged_textures[material_id]
            
        metallic_file = self.find_texture('R', material_id, 'Metallic')
        roughness_file = self.find_texture('R', material_id, 'Roughness')
        
        if not metallic_file or not roughness_file:
            return roughness_file or metallic_file
            
        merged_name = f'merged_{material_id}_MetallicRoughness.jpeg'
        merged_path = self.work_dir / merged_name
        
        if merged_path.exists():
            self.merged_textures[material_id] = merged_name
            return merged_name
            
        print(f"  合并 Metallic/Roughness: {material_id}")
        met = Image.open(self.work_dir / metallic_file).convert('L')
        rough = Image.open(self.work_dir / roughness_file).convert('L')
        
        # glTF 标准: R=未使用(0), G=Roughness, B=Metallic
        r_channel = Image.new('L', met.size, 0)
        merged = Image.merge('RGB', [r_channel, rough, met])
        merged.save(merged_path, quality=95)
        
        self.merged_textures[material_id] = merged_name
        return merged_name
        
    def build_material(self, material_id: str, is_opacity: bool = False) -> dict:
        """为指定材质编号构建 glTF material 对象"""
        mat_name = f"{material_id}_Mat" if material_id not in ('Smoke', 'Water', 'Water_1') else material_id
        mat = {
            "doubleSided": True,
            "name": mat_name,
            "pbrMetallicRoughness": {
                "metallicFactor": 1.0,
                "roughnessFactor": 1.0
            }
        }
        
        if material_id == 'Smoke':
            mat["pbrMetallicRoughness"]["baseColorFactor"] = [0.02, 0.02, 0.02, 0.25]
            mat["alphaMode"] = "BLEND"
            return mat
            
        # 查找贴图
        basecolor = self.find_texture('RGB', material_id, 'BaseColor')
        normal = self.find_texture('N', material_id, 'Normal')
        emissive = self.find_texture('RGB', material_id, 'Emissive')
        
        # 查找并合并 Metallic/Roughness
        merged_mr = self.get_merged_metallic_roughness(material_id)
        
        if basecolor:
            mat["pbrMetallicRoughness"]["baseColorTexture"] = {"index": self.add_texture(basecolor)}
        if merged_mr:
            mat["pbrMetallicRoughness"]["metallicRoughnessTexture"] = {"index": self.add_texture(merged_mr)}
        if normal:
            mat["normalTexture"] = {"index": self.add_texture(normal)}
        if emissive:
            mat["emissiveTexture"] = {"index": self.add_texture(emissive)}
            mat["emissiveFactor"] = [1.0, 1.0, 1.0]
            
        # 尝试查找 AO 贴图 (命名较自由，模糊匹配)
        ao = self.find_ao_texture(material_id)
        if ao:
            mat["occlusionTexture"] = {"index": self.add_texture(ao)}
            
        if is_opacity or material_id in ('Water', 'Water_1'):
            mat["alphaMode"] = "BLEND"
            if not basecolor:
                mat["pbrMetallicRoughness"]["baseColorFactor"] = [0.8, 0.8, 0.8, 0.75]
                
        return mat
        
    def find_ao_texture(self, material_id: str) -> str:
        """模糊查找 AO/AmbientOcclusion 贴图"""
        for f in self.texture_files:
            if 'AO' in f.upper() or 'AMBIENT' in f.upper() or 'OCCLUSION' in f.upper():
                # 检查文件名是否包含当前 material_id 或相关编号
                if re.search(r'[\W_]' + re.escape(material_id) + r'[\W_]', f):
                    return f
        return None
        
    def add_texture(self, filename: str) -> int:
        """向 images/textures 数组添加贴图引用，返回 texture 索引"""
        if not filename:
            return None
        for i, img in enumerate(self.images):
            if img['uri'] == filename:
                return i
        idx = len(self.images)
        self.images.append({"uri": filename})
        self.textures.append({"sampler": 0, "source": idx})
        return idx
        
    def repair(self):
        """执行修复主流程"""
        self.load()
        
        # 初始化 glTF 贴图数组
        self.images = []
        self.textures = []
        self.samplers = [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}]
        
        # 分析 mesh -> material_id 映射
        mesh_to_id = {}
        unique_ids = set()
        for i, mesh in enumerate(self.data.get('meshes', [])):
            mid = self.extract_material_id(mesh['name'])
            mesh_to_id[i] = mid
            if mid:
                unique_ids.add(mid)
                
        print(f"发现 {len(unique_ids)} 个唯一材质编号: {sorted(unique_ids)}")
        
        # 为每个唯一编号构建 material
        materials_dict = {}
        for mid in sorted(unique_ids):
            materials_dict[mid] = self.build_material(mid, is_opacity=False)
            # 如果存在透明变体，也创建
            opacity_key = f"{mid}_Opacity"
            # 这里简化处理：如果目录中有 Opacity 贴图或 mesh 名称包含 Opacity，则创建
            has_opacity_mesh = any(
                mesh_to_id[i] == mid and self.is_opacity_mesh(self.data['meshes'][i]['name'])
                for i in mesh_to_id
            )
            if has_opacity_mesh:
                op_mat = copy.deepcopy(materials_dict[mid])
                op_mat["name"] = f"{mid}_Opacity"
                op_mat["alphaMode"] = "BLEND"
                materials_dict[opacity_key] = op_mat
                
        # 排序并分配索引
        material_keys = []
        for mid in sorted(unique_ids):
            material_keys.append(mid)
            opacity_key = f"{mid}_Opacity"
            if opacity_key in materials_dict:
                material_keys.append(opacity_key)
                
        key_to_index = {}
        new_materials = []
        for key in material_keys:
            key_to_index[key] = len(new_materials)
            new_materials.append(materials_dict[key])
            
        # 更新 mesh 的 material 引用
        for i, mesh in enumerate(self.data.get('meshes', [])):
            mid = mesh_to_id.get(i)
            if not mid:
                continue
            key = mid
            if self.is_opacity_mesh(mesh['name']):
                opacity_key = f"{mid}_Opacity"
                if opacity_key in key_to_index:
                    key = opacity_key
            if key in key_to_index:
                mesh['primitives'][0]['material'] = key_to_index[key]
                
        # 写回 glTF 数据
        self.data['materials'] = new_materials
        if self.images:
            self.data['images'] = self.images
        if self.textures:
            self.data['textures'] = self.textures
        if self.samplers:
            self.data['samplers'] = self.samplers
            
        # 保存
        backup_path = self.gltf_path.with_suffix('.gltf.bak')
        if not backup_path.exists():
            print(f"备份原文件: {backup_path.name}")
            self.gltf_path.rename(backup_path)
            
        output_path = self.gltf_path
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)
            
        print(f"\n修复完成!")
        print(f"  Materials: {len(new_materials)}")
        print(f"  Images: {len(self.images)}")
        print(f"  Textures: {len(self.textures)}")
        print(f"  合并贴图: {len(self.merged_textures)} 个")
        print(f"  输出: {output_path.name}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print(f"用法: python {sys.argv[0]} <gltf_file>")
        sys.exit(1)
        
    gltf_file = sys.argv[1]
    if not os.path.exists(gltf_file):
        print(f"错误: 文件不存在: {gltf_file}")
        sys.exit(1)
        
    repair = GltfTextureRepair(gltf_file)
    repair.repair()


if __name__ == '__main__':
    main()
