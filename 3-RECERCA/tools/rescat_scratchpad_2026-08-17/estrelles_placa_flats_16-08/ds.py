import json,sys,urllib.parse,subprocess
q=sys.argv[1]
u="https://dspace.vut.cz/server/api/discover/search/objects?query="+urllib.parse.quote(q)+"&size=20&dsoType=item"
out=subprocess.run(["curl","-sL","--max-time","60","-H","Accept: application/json",u],capture_output=True).stdout
d=json.loads(out)
objs=d['_embedded']['searchResult']['_embedded']['objects']
for o in objs:
    io=o['_embedded']['indexableObject']
    m=io['metadata']
    t=m.get('dc.title',[{}])[0].get('value','')
    y=m.get('dc.date.issued',[{}])[0].get('value','')
    au=[a['value'] for a in m.get('dc.contributor.author',[])]
    uid=io['uuid']
    print('==',y,'|',t[:110],'|',', '.join(au[:5]))
    bu=f"https://dspace.vut.cz/server/api/core/items/{uid}/bundles"
    b=json.loads(subprocess.run(["curl","-sL","--max-time","60","-H","Accept: application/json",bu],capture_output=True).stdout)
    for bun in b.get('_embedded',{}).get('bundles',[]):
        if bun['name']!='ORIGINAL': continue
        su=f"https://dspace.vut.cz/server/api/core/bundles/{bun['uuid']}/bitstreams"
        s=json.loads(subprocess.run(["curl","-sL","--max-time","60","-H","Accept: application/json",su],capture_output=True).stdout)
        for bs in s.get('_embedded',{}).get('bitstreams',[]):
            print('    FILE:',bs['name'],bs['sizeBytes'],'https://dspace.vut.cz/bitstreams/%s/download'%bs['uuid'])
