#!/usr/bin/env node

var fs = require('fs'),
    child_process = require('child_process'),
    prependFile = require('prepend-file'),
    params = [],
    comments = '',
    type = '',
    filePath = 'CHANGELOG.md',
    gitList = ['b','c','clone','init','add','mv','reset','rm','bisect','grep','log','show','status','branch','checkout','commit','diff','merge','rebase','tag','fetch','pull','push'];

var verReg = /\#\#\#\#\#\s\d+\.\d+\.\d+\.(\d)+/g;
var verLineCount = 0; // verReg 计数器，记录其在数据中的索引

var argvsMap = {};
var argvs = (function(){
    var arr = [];
    process.argv.forEach(function(v,i){
        if(v !== '-x'){
            arr.push(v);
        }
        argvsMap[v] = true;
    });
    return arr.slice(2);
})();

function initParams(){

    new Promise(function(reslove, reject){
        var key = argvs[0];
        if(key){
            if(gitList.indexOf(key) !== -1){
                argvs.unshift('git');
                if(key === 'branch' || key === 'b'){ //新增分支
                    var branch = getValue(key);
                    getNewVersion().then(function(newVersion){
                        console.log('新建分支', newVersion);
                        _write('addver', '\n' + newVersion + '\n',function(){
                            reslove();
                        });
                    });
                }else if(key === 'commit' || key === 'c'){
                    var commit = getValue(key)
                    console.log('提交修改', commit);
                    _write('commit', commit && '* ' + commit || '',function(){
                        reslove();
                    });
                }else{
                    reslove()
                }
            }
        }else{
            reslove();
        }
    })
    .then(function(){
        execute(argvs);
    });
}

function _writeCommit(val, callback) {
    var lines = fs.readFileSync(filePath, 'utf8').split('\n');
    for(var i = 0; i < lines.length; i++) {
        var line = lines[i];
        if(line.match(verReg)) {
            verLineCount++;
            if(verLineCount === 2) {
                lines.splice((i - 1), 0, val);
                var text = lines.join('\n');
                fs.writeFile(filePath, text, function(err, res) {
                    if(err) return console.log(err);
                    callback && callback();
                });
                return;
            }
        }
    }

    if(verLineCount === 1) {
        fs.appendFile(filePath, '\n' + val, 'utf8', function(err) {
            if(err) throw err;
            callback && callback();
        });
    } else {
        var ret = [];
        ret.push('\n\n' + getLastesVer(filePath) + '\n');
        ret.push(val);
        fs.appendFile(filePath, ret.join('\n'), 'utf8', function(err) {
            if(err) throw err;
            callback && callback();
        })
    }
}

function _write(type, val,callback){
    var typeMap = {
        'addver': prependFile,
        'commit': fs.appendFile
    }
    if(!val){
        console.log('未输入修改信息');
        callback && callback();
        return;
    }

    if(type === 'addver') {
        prependFile(filePath, '\n' + val ,'utf8',function(err){
            if (err){
                throw err;
            }else{
                callback && callback();
            }
        });   
    }
    if(type === 'commit') {
        _writeCommit(val, callback);
    }

}

function getValue(key){
    var flag = false,value = '';
    if(argvsMap['-x']){
        return '';
    }
    for(var i=0,len=argvs.length;i<len;i++){
        var v = argvs[i];
        if(v === key){
            flag = true;
            continue;
        }
        if(flag && !v.match(/^\-/g)){
            value = v;
            continue;
        }
    }
    return value;
}

function getLastesVer(filePath) {
    var lineArr = fs.readFileSync(filePath, 'utf8').split('\n');
    var ver = '##### 1.0.0.0';

    for(var i = 0, len = lineArr.length; i < len; i++) {
        var line = lineArr[i];
        if(line && line.match(verReg)) {
            var position = line.lastIndexOf('.');
            var localVer = line.substr(position+1).match(/\d+/);
            localVer = localVer && localVer[0] || 0;
            localVer = parseInt(localVer,10) + 1;
            var nativeVer = line.substr(0,position+1);
            ver = nativeVer + localVer;
            return ver;
        }
    }

    return ver;
}

function getNewVersion(){
    var ver = '';
    var p = new Promise(function(reslove,reject){
        fs.exists(filePath,function(bool){
            if(bool){
                reslove(getLastesVer(filePath));
            }else{
                // 1.0.0 = native 版本，最后一位是本地版本
                ver = '##### 1.0.0.0';
                console.log('version name : ', ver);
                reslove(ver);
            }
        });
    });
    return p;
}

function execute(){
    var commands = argvs.map(function(v){
        if(v.match(/\s/gi)){
            return ('"' + v + '"');
        }else{
            return v;
        }
    }).join(' ');
    child_process.exec(commands , function(err,stdout,stderr){
        if(err){
            console.log('-----------------------')
            console.log(commands);
            console.log(stdout);
            console.log('execute fail');
            console.log('-----------------------')
        }else{
            console.log('-----------------------')
            stdout && console.log(stdout);
            console.log('execute success');
            console.log('-----------------------')
        }
    });
}


initParams();
