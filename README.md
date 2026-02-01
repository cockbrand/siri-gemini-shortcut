To be called by an Apple Shortcut, see screenshot for configuration.  
Runs as a Cloud Run Function. You need to add the API key to the GEMINI_API_KEY environment variable in your instance.  

Deployment:  
`gcloud run deploy siri-gemini-bridge \                                                                                                                                                            [ 10:16:57 ]
  --source . \
  --function siri_gemini \
  --base-image python312 \
  --region ${REGION} \
  --allow-unauthenticated`

Setting the environment variable:  
`gcloud run deploy siri-gemini-bridge \
  --set-env-vars GEMINI_API_KEY=${API_KEY}`

N.B. that the API Key is a secret and should be put into Secret Manager as a best practice, depending on your security requirements.

Trigger: "[Hey ]Siri, ask Gemini"  

![Screenshot of Apple Shortcut](https://github.com/cockbrand/siri-gemini-shortcut/blob/main/Apple%20Shortcut.png)
