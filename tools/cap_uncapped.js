conn = new Mongo();
db = conn.getDB('backdrop');
var capped = [];
var uncapped_realtime = [];
db.getCollectionNames().forEach(function(collname) {
    var stats = db[collname].stats();
    var realtime = collname.match('realtime');
    if (stats['capped'] == true) {
      if (!realtime) {
        capped.push(collname)
      }
    } else {
      if (realtime) {
        uncapped_realtime.push(collname)
        print('capping ' + collname)
        db.runCommand({"convertToCapped": collname, size: 4194304 });
      }
    }
});

print('capped non realtime');
print(capped.join("\n"));
print('uncapped realtime');
print(uncapped_realtime.join("\n"));

