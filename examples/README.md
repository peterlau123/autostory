# Autostory Examples

This directory contains example scripts demonstrating how to use various AI platforms integrated with the autostory project.

## Platform Examples

### Volcengine Jimeng Text-to-Image

**File:** `examples/volcengine/example_jimeng_text2image.py`

This example demonstrates how to use the Volcengine Jimeng API to generate images from text prompts.

#### Features Demonstrated:
- Text-to-image generation with Chinese prompts
- Automatic credential management using environment variables or `.access.json`
- Parameter configuration (dimensions, retry logic, etc.)
- Error handling and user feedback
- Reference image support (optional)
- **Automatic local image saving** - Downloads and saves generated images to the `generated_images/` subdirectory

#### Setup Requirements:

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Credentials** (choose one option):

   **Option A: Environment Variables**
   ```bash
   export VOLCENGINE_ACCESS_KEY_ID=your_access_key_here
   export VOLCENGINE_SECRET_KEY=your_secret_key_here
   ```

   **Option B: .access.json File**
   Create `.access.json` in the project root:
   ```json
   {
     "platforms": {
       "volcengine": {
         "access_key_id": "your_access_key_here",
         "secret_key": "your_secret_key_here"
       }
     }
   }
   ```

#### Usage:

```bash
# Run the main example
python examples/volcengine/example_jimeng_text2image.py

# Show parameter examples
python examples/volcengine/example_jimeng_text2image.py --examples
```

#### Sample Output:
```
🎨 Volcengine Jimeng Text-to-Image Generation Example
============================================================
Prompt: 金军来袭，北宋汴京，人来人往
Dimensions: 1024x1024
Reference images: 0 provided

🔧 Initializing Volcengine Image Generator...
🚀 Starting image generation...
This may take 30-60 seconds depending on server load.

✅ Generation completed successfully!
----------------------------------------
Task ID: abc123def456
Generated images: 1

📸 Generated Image URLs:
  1. https://generated-image-url.com/image.jpg

💾 Downloading and saving images...
📥 Downloading image 1/1...
✅ Saved to: /path/to/examples/volcengine/generated_images/generated_image_20231201_143022_1.jpg

✅ Successfully saved 1 image(s) to local directory:
📁 Location: /path/to/examples/volcengine/generated_images
  📄 generated_image_20231201_143022_1.jpg

💡 Tip: Images have been saved locally for offline viewing.
```

## Adding New Examples

When adding new examples:

1. Create a subdirectory for the platform (e.g., `examples/openai/`)
2. Include comprehensive setup instructions in the script docstring
3. Provide clear usage examples and expected output
4. Handle errors gracefully with helpful messages
5. Update this README.md with the new example information

## General Setup

All examples require:
- Python 3.8+
- Dependencies listed in `requirements.txt`
- Proper API credentials configured
- Stable internet connection

## Troubleshooting

**Import Errors:** Make sure you're running examples from the project root directory.

**Credential Errors:** Check that your API credentials are properly configured using either environment variables or the `.access.json` file.

**Network Issues:** Ensure you have a stable internet connection and the target API service is operational.
