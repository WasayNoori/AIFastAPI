# PowerShell script to test /analyzetext endpoint using curl

# Read your script from a file
$scriptContent = Get-Content -Path "your_script.txt" -Raw

# Escape the content for JSON
$escapedContent = $scriptContent -replace '\\', '\\' -replace '"', '\"' -replace "`r`n", '\n' -replace "`n", '\n'

# Build the JSON payload
$jsonPayload = @{
    text = $scriptContent
    language = "en"
    correct_grammar = $false
} | ConvertTo-Json

# Send the request
$headers = @{
    "Authorization" = "Bearer YOUR_JWT_TOKEN_HERE"
    "Content-Type" = "application/json"
}

$response = Invoke-RestMethod -Uri "http://localhost:8000/translation/analyzetext" `
    -Method Post `
    -Headers $headers `
    -Body $jsonPayload

# Display the response
$response | ConvertTo-Json -Depth 10
