
var PythonShell = require('python-shell');
var PY_FILE_NAME = 'query_make_t_bkw3.py';

// var run = (pyfilepath) =>{
//   PythonShell.run(pyfilepath, (err,results)=> {
//     if (err) throw err;
//     console.log(results);
//     console.log('finished');
//   });
// }

const pShellOn = (pyfilepath,msg) => {
  return new Promise((resolve,reject)=>{
    shellOn(resolve,reject,pyfilepath,msg)
  });
}

const shellOn = (resolve,reject,pyfilepath,msg) =>{
  // var pyShell = new PythonShell(pyfilepath, {mode : 'json', args : [msg] });
  var pyShell = new PythonShell(pyfilepath, {mode : 'text', args : [msg] ,pythonPath : 'python27.exe'});
  //var pyShell = new PythonShell(pyfilepath, {mode : 'json', args : [msg] ,pythonPath : 'python27.exe'});
  // var pyShell = new PythonShell(pyfilepath, {mode : 'json' });
  pyShell.on('message',(result)=>{
    //console.log(result)
    resolve(result);
  });
  pyShell.end((err)=>{
    if(err) throw err;
  })
}

// debug -------------------------
// -------------------------------
if(require.main === module){
  var main = () =>{
    var msg_ = 'Excelについて教えて';
    pShellOn(PY_FILE_NAME,msg_)
      .then((result)=>{
        console.log(result);
      })
      .catch((err)=>{
        console.dir(err);
      });
  }
  main();
}
