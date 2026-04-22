from pathlib import Path
import inspect
import mcp.server.fastmcp.server as server

print('server file:', inspect.getsourcefile(server))

src = Path(inspect.getsourcefile(server)).read_text()
for term in ['Missing session ID', 'session_id', 'Accept: application/json', 'text/event-stream', 'Not Acceptable']:
    if term in src:
        print('===', term, '===')
        idx = src.index(term)
        print(src[max(0, idx-200):idx+200])
