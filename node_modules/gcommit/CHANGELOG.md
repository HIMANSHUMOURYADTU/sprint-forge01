
##### 1.0.0.5

* 修改最新的日志在文件顶部

##### 1.0.0.4

* 新增新的缩写
* 新增不需要手动输入git就可以直接执行git命令 移除了第三方控件的引用
* 移除了 -c/-commit/-b/-branch 的命令，直接执行gtc commit/c/branch/b就可以把修改信息写入changelog
* 提供了 -x 参数，加上这两个参数comments信息将不会写入changelog
* 啊哈哈哈哈，ugc好厉害

##### 1.0.0.3

* gtc -c/-commit 提交修改
* gtc -b/-branch 新建分支，将会自增一个新版本在changelog里
* gtc 任意命令会直接执行该命令
* add yargs
