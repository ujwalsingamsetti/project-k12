# Google Cloud Vision API Setup Instructions

## The Error
```
File ./google-vision-credentials.json was not found.
```

## Solution: Create Google Cloud Vision Credentials

### Option 1: Get Real Credentials (Recommended for Production)

1. **Go to Google Cloud Console**: https://console.cloud.google.com/

2. **Create a Project** (if you don't have one):
   - Click "Select a project" → "New Project"
   - Name it "k12-evaluator"
   - Click "Create"

3. **Enable Vision API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Cloud Vision API"
   - Click "Enable"

4. **Create Service Account**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "Service Account"
   - Name: "k12-ocr-service"
   - Click "Create and Continue"
   - Role: "Cloud Vision API User"
   - Click "Done"

5. **Download JSON Key**:
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose "JSON"
   - Click "Create"
   - Save the downloaded file as `google-vision-credentials.json`

6. **Place the file**:
   ```bash
   mv ~/Downloads/your-project-*.json /Users/ujwalsingamsetti/project-k12/k12-answer-evaluator/backend/google-vision-credentials.json
   ```

### Option 2: Use Mock/Dummy Credentials (For Testing Without API)

If you don't want to use Google Vision API right now, you can create a dummy file:

```bash
cd /Users/ujwalsingamsetti/project-k12/k12-answer-evaluator/backend
cat > google-vision-credentials.json << 'EOF'
{
  "type": "service_account",
  "project_id": "dummy-project",
  "private_key_id": "dummy-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nDUMMY\n-----END PRIVATE KEY-----\n",
  "client_email": "dummy@dummy-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/dummy%40dummy-project.iam.gserviceaccount.com"
}
EOF
```

**Note**: With dummy credentials, the OCR will fail, but the app won't crash on startup.

### Option 3: Disable Google Vision (Use Tesseract Instead)

Modify the code to make Google Vision optional and fall back to Tesseract.

## Pricing Information

- **Free Tier**: First 1,000 requests per month are FREE
- **After Free Tier**: $1.50 per 1,000 images
- **Document Text Detection**: Same pricing as above

For a school with 100 students submitting 10 papers each = 1,000 submissions/month = FREE!

## Quick Setup Command

```bash
# Navigate to backend
cd /Users/ujwalsingamsetti/project-k12/k12-answer-evaluator/backend

# Create dummy credentials (for testing)
cat > google-vision-credentials.json << 'EOF'
{
  "type": "service_account",
  "project_id": "k12-evaluator-test",
  "private_key_id": "test123",
  "private_key": "-----BEGIN PRIVATE KEY-----\nTEST_KEY\n-----END PRIVATE KEY-----\n",
  "client_email": "test@k12-evaluator-test.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
}
EOF

echo "✅ Dummy credentials created. Replace with real credentials for production."
```

## Verify Setup

```bash
# Check if file exists
ls -la google-vision-credentials.json

# Restart backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Alternative: Use Environment Variable

Instead of a file, you can set the credentials as an environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/google-vision-credentials.json"
```

Add this to your `.bashrc` or `.zshrc` for persistence.
