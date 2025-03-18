Few Important points:
1. To run this code,
ffmpeg should be installed in your PC. and bin PATH must be updated to Environment SYSTEM PATH

2.For now, Run chrome after the disabling CORS security feature to process

For Windows
Close all Chrome instances.
Press Win + R, type cmd, and press Enter.
Run the following command:

chrome.exe --disable-web-security --user-data-dir="C:\chrome_dev"

3. Open client_demo.html with chrome instance launched in step 2.

4. Browse a short video for quicker results and click on analyze_video button. ( Prior doing this ensure the execution of the Python code)
5. Ensure INFO:     Uvicorn running on http://0.0.0.0:8000 in Terminal logs for python
6. AI model used gemini-1.5-flash
7. For sample output(json format) of the video_description_api project, pls refer sample_output.txt 
   PS: the output file is for one example video, and it contains the debug prints also.