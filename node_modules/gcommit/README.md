#### README
--------------------------------------------------------------------------------

#### **安装方法**：
* npm install gcommit -g

#### **插件介绍**：
* 提交git修改时自动把修改内容写入CHANGELOG
* 新建git分支时自动把版本号写入CHANGELOG
* 没有CHANGELOG时自动新增CHANGELOG.md

#### **使用方法**：
* gtc加任意命令名即可使用，主要针对git命令使用
* 如果是git命令可以直接gtc加git命令名，如gtc pull、gtc commit -am '这是一次提交'<br/>注释会被当成CHANGELOG中的一条新信息
* 不想把修改信息写入CHANGELOG时可以加 -x 即可。
* gtc branch 在当前分支打一个新版本
* 如果是其他命令就gtc加命令名，如gtc ls、gtc ls -l。所以其实没什么卵用


#### **新增**：
* changelog显示顺序从新到旧
