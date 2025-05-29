import os
import base64
import tempfile
from openai import OpenAI
from PIL import Image

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
age = 2
gender = "male"
race = "white"
expression = "happy"
hairstyle = "short hair"
clothing = "t-shirt"
accessories = "glasses"
pose = "standing"
lighting = "natural light"
background = "outdoor"
environment = "city"
mood = "happy"
atmosphere = "relaxed"
style = "realistic"
composition = "centered"


def prepare_image(image_path, is_base64=False):
    """Convert image to RGBA format and save to temporary file"""
    img = Image.open(image_path).convert("RGBA")
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(temp_file, format="PNG")
    temp_file.close()  # Close file for later reopening
    if is_base64:
        return base64.b64encode(temp_file.read()).decode("utf-8")
    return temp_file.name

# Configuration
source_image_path = "storage/0150dbb9-4f4a-44f1-b501-70772da1ab5a.png"  # Image with face to USE
target_image_path = "storage/7133bfe9-0f8d-467f-80b6-4c2e5445561b.jpeg"  # Image with face to REPLACE
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Prepare images with proper file extensions
source_temp = prepare_image(source_image_path, False)
target_temp = prepare_image(target_image_path, False)

# Face swap prompt - refined instructions
prompt_edit = (
    "PRECISE FACE SWAP: Replace the face in the source image with the face from the target image. "
    "Maintain the source image's:\n"
    "- Head position and orientation\n"
    "- Lighting conditions and shadows\n"
    "- Skin tone and texture\n"
    "- Background details\n"
    "- Facial expression intensity\n"
    "Seamlessly blend the face edges. Preserve all non-facial elements exactly. "
    "Ensure natural positioning of eyes, nose, and mouth. Avoid distortions."
    "The age of the person in the source image will be " + age + " years old\n"
    "The gender of the person in the source image will be " + gender + "\n"
    "The race of the person in the source image will be " + race + "\n"
    "The expression of the person in the source image will be " + expression + "\n"
    "The hairstyle of the person in the source image will be " + hairstyle + "\n"
    "The clothing of the person in the source image will be " + clothing + "\n"
    "The accessories of the person in the source image will be " + accessories + "\n"
    "The pose of the person in the source image will be " + pose + "\n"
    "The lighting of the person in the source image will be " + lighting + "\n"
    "The background of the person in the source image will be " + background + "\n"
    "The environment of the person in the source image will be " + environment + "\n"
    "The mood of the person in the source image will be " + mood + "\n"
    "The atmosphere of the person in the source image will be " + atmosphere + "\n"
    "The style of the person in the source image will be " + style + "\n"
    "The composition of the person in the source image will be " + composition + "\n"
)

try:
    # Generate the face-swapped image using file handles
    with open(source_temp, "rb") as src_file, open(target_temp, "rb") as tgt_file:
        response = client.images.edit(
            model="gpt-image-1",
            image=[src_file, tgt_file], 
            prompt=prompt_edit,
            size="1024x1024",
        )

    print("Response:")
    print(response)
    # Save the result
    image_data = base64.b64decode(response.data[0].b64_json)
    output_path = os.path.join(output_dir, "face_swap_result.png")
    
    with open(output_path, "wb") as f:
        f.write(image_data)
    
    print(f"✅ Face swap generated successfully at:\n{output_path}")

finally:
    # Clean up temporary files
    os.unlink(source_temp)
    os.unlink(target_temp)
    print("Temporary files cleaned up")