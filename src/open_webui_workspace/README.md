# Open WebUI Workspace

PRE-REQ: Read the Open WebUI installation guide and have Open WebUI Workspace accessible. See https://docs.openwebui.com/getting-started/
For easiest setup use a Docker container. Your URL will be something like http://localhost:8080.

Guide on how to use the Open WebUI Workspace:
1. The first thing you will do is set up a .env file! You can use the example-env.txt file as a template.
```
cd screenpipe-python-client
cp example-env.txt .env
```
2. Ensure you have a valid endpoint and API key for the LLM(s) you want to use. The default uses Ollama with Qwen2.5 models, but you can change this in the .env file, or with Valves
3. Ensure you are signed into Open WebUI. Navigate via the UI or use {URL}/workspace/functions to get to the functions page.
4. Add the Filter and Pipe Functions to your Open WebUI workspace. Ensure you are signed on, then follow the one-time function setup instructions below. This will be made much easier in the future. (Using JSON configuration directly at OWUI setup).

To add the Filter Function:
- Copy the code in screenpipe_filter_function.py.
- I recommend naming it Filter.
- Workspace > Functions > Add Function > Any Name + Description + Paste screenpipe_filter_function.py code > Save > Functions > ENABLE IT! (Toggled off by default)

To add the Pipe Function:
- Copy the code in simple_search_function.py.
- I recommend naming it ScreenPipe.
- Workspace > Functions > Add Function > Any Name + Description + Paste simple_search_function.py code > Save > Functions > ENABLE IT! (Toggled off by default)
- Navigate to {URL}/workspace/models/edit?id=screenpipe or search for your new pipe model in Workspace > Models bar and click edit.
- IMPORTANT: Filters > Tick the Checkbox for Filter. This is how the Pipe knows to use the Filter! (Ensure both are turned on in the Functions page)

Last step:
5. Navigate 
```
cd screenpipe-python-client
```
- You can now use the Pipe function in your chat!
- Change any values in the Valves section, or in your .env file at server start.


TODO: Visual guide