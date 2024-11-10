import os
from datetime import datetime
from typing import Literal, Tuple
from urllib.parse import urlparse
import httpx
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

# Load .env file
load_dotenv()

__IMAGES_BASE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data/images')

def get_all_images() -> pd.DataFrame:
    """
    Retrieves a DataFrame containing information about all images stored in a folder.
    """
    # 確保資料夾存在
    if not os.path.exists(__IMAGES_BASE_FOLDER):
        return pd.DataFrame(columns=['Image', 'Description', 'Date Created'])
    
    # 初始化列表來存儲資料
    image_data = []
    
    # 遍歷資料夾中的所有檔案
    for filename in os.listdir(__IMAGES_BASE_FOLDER):
        if filename.endswith('.png'):
            image_path = os.path.join(__IMAGES_BASE_FOLDER, filename)
            txt_path = os.path.join(__IMAGES_BASE_FOLDER, f"{os.path.splitext(filename)[0]}.txt")
            
            # 獲取建立時間
            creation_time = datetime.fromtimestamp(os.path.getctime(image_path))
            
            # 讀取描述檔案
            description = ""
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f:
                    description = f.read().strip()
            
            image_data.append({
                'Image': image_path,
                'Description': description,
                'Date Created': creation_time
            })
    
    # 創建並返回 DataFrame
    df = pd.DataFrame(image_data)
    if len(df) == 0:
        return df
    return df.sort_values('Date Created', ascending=False)

def delete_image(image_path: str):
    """
    Deletes an image file and its associated description file.
    """
    try:
        # 刪除圖片檔案
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # 刪除對應的描述檔案
        txt_path = os.path.splitext(image_path)[0] + '.txt'
        if os.path.exists(txt_path):
            os.remove(txt_path)
            
    except Exception as e:
        raise Exception(f"Error deleting files: {str(e)}")



async def generate_image(
    prompt: str,
    model: str = "dall-e-3",
    style: Literal["vivid", "natural"] = "vivid",
    quality: Literal["standard", "hd"] = "hd",
    timeout: int = 100,
    size: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] = "1024x1024"
) -> Tuple[str, str]:
    """
    Generates an image using OpenAI's DALL-E model and saves it locally.
    """
    try:
        # 確保儲存資料夾存在
        os.makedirs(__IMAGES_BASE_FOLDER, exist_ok=True)
        
        # 初始化 OpenAI 客戶端
        client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_API_BASE_URL'))
        
        # 生成圖片 - 這裡使用同步調用
        response = client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            style=style,
            n=1
        )
        
        # 獲取圖片 URL
        image_url = response.data[0].url
        
        # 下載圖片
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            
            # 生成檔案名稱
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}.png"
            filepath = os.path.join(__IMAGES_BASE_FOLDER, filename)
            
            # 儲存圖片
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # 儲存提示文字
            txt_filepath = os.path.join(__IMAGES_BASE_FOLDER, f"image_{timestamp}.txt")
            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write(prompt)
            
            return prompt, filepath
            
    except Exception as e:
        raise Exception(f"Error generating image: {str(e)}")

def _extract_filename_from_url(url: str) -> str:
    """
    Extracts the filename from a URL.
    """
    # 解析 URL
    parsed_url = urlparse(url)
    
    # 獲取路徑
    path = parsed_url.path
    
    # 提取檔案名稱
    filename = os.path.basename(path)
    
    # 如果沒有副檔名，添加 .png
    if not os.path.splitext(filename)[1]:
        filename += '.png'
    
    return filename