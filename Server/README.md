# E-Hospital Prescription Backend Testing Instructions
## Frontend Testing
You can interact with the backend through the frontend:

URL: https://e-hospital-client.onrender.com/

Steps:

1. Open the link in a browser.

2. In the text input field, paste:

"Patient: John Doe, Diagnosis: Fatty Liver. Warfarin 500mg capsules, 1 capsule by mouth three times daily for 10 days, 30 capsules, 0 Refills. Also, Ibuprofen 200mg, 1-2 tablets by mouth every 4-6 hours as needed for pain, 60 tablets, 2 refill. Rifaximin 550mg tablets Dosage: 1 tablet three times daily for 3 days. Quantity: 9 tablets, Refills: 0 Note: Take Warfarin with food to avoid stomach upset."

3. Click "Send".

## Postman
- Postman installed (download from https://www.postman.com/downloads/).
- An audio file (e.g., `.wav`) for testing `/transcribe_stream`.



## Testing the Endpoints
### 1. /chat 
- **Method**: POST
- **URL**: `https://e-hospital-prescription-294a0e858fcd.herokuapp.com/chat`
- **Body**:   
  ```json{
   { "text" : "Patient: John Doe, Diagnosis: Fatty Liver. Warfarin 500mg capsules,  1 capsule by mouth three times daily for 10 days, 30 capsules, 0 Refills. Also, Ibuprofen 200mg , 1-2 tablets by mouth every 4-6 hours as needed for pain, 60 tablets, 2 refill. Rifaximin 550mg tablets Dosage: 1 tablet three times daily for 3 days.Quantity: 9 tablets, Refills: 0 Note: Take Warfarin with food to avoid stomach upset."
  }
             
