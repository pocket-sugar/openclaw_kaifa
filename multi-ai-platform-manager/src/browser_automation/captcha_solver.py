"""
验证码识别模块
支持多种验证码类型：数字、字母、滑块、点选等
"""

import base64
import io
import logging
import re
import time
from typing import Optional, Tuple, Dict, Any
from PIL import Image
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CaptchaSolver:
    """验证码识别器基类"""
    
    def __init__(self):
        self.success_rate = 0.0
        self.total_attempts = 0
        self.successful_attempts = 0
        
    async def solve(self, image_data: bytes, captcha_type: str = "digit") -> Optional[str]:
        """
        识别验证码
        
        Args:
            image_data: 验证码图片数据
            captcha_type: 验证码类型 (digit, letter, slide, click, etc.)
            
        Returns:
            Optional[str]: 识别结果
        """
        self.total_attempts += 1
        
        try:
            result = await self._solve_impl(image_data, captcha_type)
            if result:
                self.successful_attempts += 1
                self.success_rate = self.successful_attempts / self.total_attempts
                logger.info(f"验证码识别成功: {result} (成功率: {self.success_rate:.2%})")
            else:
                logger.warning("验证码识别失败")
                
            return result
            
        except Exception as e:
            logger.error(f"验证码识别出错: {e}")
            return None
            
    async def _solve_impl(self, image_data: bytes, captcha_type: str) -> Optional[str]:
        """具体实现，由子类重写"""
        raise NotImplementedError("子类必须实现此方法")
        
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_attempts": self.total_attempts,
            "successful_attempts": self.successful_attempts,
            "success_rate": self.success_rate
        }


class SimpleDigitCaptchaSolver(CaptchaSolver):
    """简单数字验证码识别器"""
    
    def __init__(self):
        super().__init__()
        
    async def _solve_impl(self, image_data: bytes, captcha_type: str = "digit") -> Optional[str]:
        """
        识别简单的数字验证码
        
        注意：这是一个简单的实现，实际使用时可能需要：
        1. 使用OCR服务（如Tesseract）
        2. 机器学习模型
        3. 第三方验证码识别API
        """
        try:
            # 将字节数据转换为PIL图像
            image = Image.open(io.BytesIO(image_data))
            
            # 转换为灰度图
            if image.mode != 'L':
                image = image.convert('L')
                
            # 二值化处理
            threshold = 128
            image = image.point(lambda x: 0 if x < threshold else 255, '1')
            
            # 简单模式匹配（示例）
            # 实际实现应该使用OCR或机器学习
            
            # 这里使用简单的规则：统计黑色像素点数量来猜测数字
            # 这只是一个演示，实际效果会很差
            pixels = np.array(image)
            black_pixels = np.sum(pixels == 0)
            total_pixels = pixels.size
            
            black_ratio = black_pixels / total_pixels
            
            # 根据黑色像素比例猜测数字（非常粗略）
            if black_ratio < 0.1:
                return "1"
            elif black_ratio < 0.2:
                return "7"
            elif black_ratio < 0.3:
                return "4"
            elif black_ratio < 0.4:
                return "2"
            elif black_ratio < 0.5:
                return "3"
            elif black_ratio < 0.6:
                return "5"
            elif black_ratio < 0.7:
                return "6"
            elif black_ratio < 0.8:
                return "8"
            elif black_ratio < 0.9:
                return "9"
            else:
                return "0"
                
        except Exception as e:
            logger.error(f"数字验证码识别失败: {e}")
            return None


class TesseractCaptchaSolver(CaptchaSolver):
    """使用Tesseract OCR的验证码识别器"""
    
    def __init__(self, tesseract_cmd: str = 'tesseract', lang: str = 'eng'):
        super().__init__()
        self.tesseract_cmd = tesseract_cmd
        self.lang = lang
        
    async def _solve_impl(self, image_data: bytes, captcha_type: str = "digit") -> Optional[str]:
        """
        使用Tesseract OCR识别验证码
        """
        try:
            # 检查是否安装了pytesseract
            try:
                import pytesseract
            except ImportError:
                logger.error("未安装pytesseract，请运行: pip install pytesseract")
                return None
                
            # 检查Tesseract是否可用
            try:
                pytesseract.get_tesseract_version()
            except Exception:
                logger.error("Tesseract未安装或路径错误")
                return None
                
            # 将字节数据转换为PIL图像
            image = Image.open(io.BytesIO(image_data))
            
            # 预处理图像
            image = self._preprocess_image(image)
            
            # 使用Tesseract识别
            config = '--psm 8 --oem 3'  # 单字符模式
            if captcha_type == "digit":
                config += ' -c tessedit_char_whitelist=0123456789'
            elif captcha_type == "letter":
                config += ' -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
            elif captcha_type == "alphanumeric":
                config += ' -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
                
            text = pytesseract.image_to_string(image, config=config, lang=self.lang)
            
            # 清理结果
            text = text.strip()
            if not text:
                return None
                
            # 移除非字母数字字符
            if captcha_type == "digit":
                text = re.sub(r'[^0-9]', '', text)
            elif captcha_type == "letter":
                text = re.sub(r'[^a-zA-Z]', '', text)
            elif captcha_type == "alphanumeric":
                text = re.sub(r'[^a-zA-Z0-9]', '', text)
                
            return text if text else None
            
        except Exception as e:
            logger.error(f"Tesseract验证码识别失败: {e}")
            return None
            
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """预处理图像以提高OCR准确率"""
        # 转换为灰度图
        if image.mode != 'L':
            image = image.convert('L')
            
        # 增强对比度
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # 二值化
        threshold = 150
        image = image.point(lambda x: 0 if x < threshold else 255, '1')
        
        # 去除噪声（简单版本）
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        return image


class DDDDCaptchaSolver(CaptchaSolver):
    """打码平台验证码识别器（示例）"""
    
    def __init__(self, api_key: str = None):
        super().__init__()
        self.api_key = api_key
        
    async def _solve_impl(self, image_data: bytes, captcha_type: str = "digit") -> Optional[str]:
        """
        使用打码平台API识别验证码
        
        注意：这是一个示例实现，需要实际的API密钥
        """
        try:
            if not self.api_key:
                logger.error("未配置打码平台API密钥")
                return None
                
            # 这里应该调用实际的打码平台API
            # 例如：超级鹰、图鉴、联众等
            
            # 示例代码结构：
            # 1. 将图片数据编码为base64
            # 2. 发送HTTP请求到打码平台
            # 3. 解析响应获取识别结果
            
            logger.info("使用打码平台识别验证码（示例）")
            
            # 模拟API调用
            await asyncio.sleep(1)  # 模拟网络延迟
            
            # 这里返回一个模拟结果
            # 实际实现应该调用真实的API
            return "1234"  # 模拟结果
            
        except Exception as e:
            logger.error(f"打码平台验证码识别失败: {e}")
            return None


class HybridCaptchaSolver(CaptchaSolver):
    """混合验证码识别器，结合多种方法"""
    
    def __init__(self):
        super().__init__()
        self.solvers = []
        
    def add_solver(self, solver: CaptchaSolver):
        """添加验证码识别器"""
        self.solvers.append(solver)
        
    async def _solve_impl(self, image_data: bytes, captcha_type: str = "digit") -> Optional[str]:
        """
        使用多个识别器尝试识别验证码
        """
        results = []
        
        for solver in self.solvers:
            try:
                result = await solver.solve(image_data, captcha_type)
                if result:
                    results.append((solver.__class__.__name__, result))
                    logger.info(f"{solver.__class__.__name__} 识别结果: {result}")
            except Exception as e:
                logger.error(f"{solver.__class__.__name__} 识别失败: {e}")
                
        if not results:
            return None
            
        # 选择最可能正确的结果
        # 这里可以使用投票机制或置信度评分
        # 简单实现：返回第一个结果
        return results[0][1]


class CaptchaManager:
    """验证码管理器"""
    
    def __init__(self):
        self.solvers = {}
        self.default_solver = None
        
    def register_solver(self, name: str, solver: CaptchaSolver, is_default: bool = False):
        """注册验证码识别器"""
        self.solvers[name] = solver
        if is_default or not self.default_solver:
            self.default_solver = solver
            
    async def solve_captcha(self, image_data: bytes, captcha_type: str = "digit", solver_name: str = None) -> Optional[str]:
        """
        识别验证码
        
        Args:
            image_data: 验证码图片数据
            captcha_type: 验证码类型
            solver_name: 指定使用的识别器名称
            
        Returns:
            Optional[str]: 识别结果
        """
        if solver_name and solver_name in self.solvers:
            solver = self.solvers[solver_name]
        elif self.default_solver:
            solver = self.default_solver
        else:
            logger.error("未找到可用的验证码识别器")
            return None
            
        return await solver.solve(image_data, captcha_type)
        
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有识别器的统计信息"""
        stats = {}
        for name, solver in self.solvers.items():
            stats[name] = solver.get_stats()
        return stats


# 工厂函数
def create_default_captcha_manager() -> CaptchaManager:
    """创建默认的验证码管理器"""
    manager = CaptchaManager()
    
    # 添加简单数字识别器
    simple_solver = SimpleDigitCaptchaSolver()
    manager.register_solver("simple_digit", simple_solver, is_default=True)
    
    # 尝试添加Tesseract识别器
    try:
        import pytesseract
        tesseract_solver = TesseractCaptchaSolver()
        manager.register_solver("tesseract", tesseract_solver)
    except ImportError:
        logger.warning("未安装pytesseract，跳过Tesseract识别器")
        
    return manager


async def test_captcha_solver():
    """测试验证码识别器"""
    print("测试验证码识别器...")
    
    # 创建一个简单的测试图像（数字4）
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    
    # 创建黑色背景的图像
    image = Image.new('RGB', (100, 50), color='white')
    draw = ImageDraw.Draw(image)
    
    # 尝试使用字体绘制数字
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
    except:
        font = ImageFont.load_default()
        
    draw.text((30, 5), "4", fill='black', font=font)
    
    # 转换为字节数据
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    image_data = img_byte_arr.getvalue()
    
    # 测试识别
    manager = create_default_captcha_manager()
    result = await manager.solve_captcha(image_data, "digit")
    
    print(f"识别结果: {result}")
    print(f"统计信息: {manager.get_all_stats()}")
    
    return result


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_captcha_solver())