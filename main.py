#! /usr/bin/env python
#coding=utf-8
import flask,paramiko,subprocess,datetime,json,os,re,threading
from flask_wtf import FlaskForm as Form
from wtforms import StringField,SubmitField,PasswordField
from wtforms.validators import Required
from flask_bootstrap import Bootstrap
from supportFunctions import checkOutput
        
app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'franknihao'
Bootstrap(app)
filePath = os.path.dirname(__file__)
'''
class chooseForm(Form):
        groupChoose = SelectField('Choose a hostgroup',choices=[(1,'a'),(2,'b')])
        hostChoose = SelectMultipleField('Choose a host',validators=[Required()],choices=[('1-01-LDZX',u'测试机器1'),('1-02-HYZX',u'测试机器2'),\
                                                                  ('1-03-HZZX',u'测试机器3'),('1-04-DJZX',u'测试机器4'),('1-05-NJZX',u'测试机器5')])
        submit = SubmitField('OK')
'''
class loginForm(Form):
        username_input = StringField(u'用户名:',validators=[Required()])
        psw_input = PasswordField(u'密码:',validators=[Required()])
        submit_button = SubmitField(u'确认')
'''
@app.route('/test')
def test():
        form = chooseForm()
        return flask.render_template('CopyOfconfig_edit.html',chooseform=form)
'''
@app.route('/')
def index():
        if flask.session.get('username') != None:
                return flask.render_template('index.html',current_time=datetime.datetime.utcnow(),user=flask.session.get('username'))
        else:
                return flask.redirect(flask.url_for('login'))
        
@app.route('/login',methods=['GET','POST'])
def login():
        form = loginForm()

        if form.validate_on_submit():
                username = form.username_input.data
                passwd = form.psw_input.data
                userCheckParam = checkUserInZabbix(username,passwd)
                if userCheckParam[0]:
                        flask.session['username'] = username
                        ssh = userCheckParam[1]
                        stdin,stdout,stderr = ssh.exec_command("python /opt/zabbixManaWeb/getGroupsForUser.py %s %s"%(username,passwd))
                        output = checkOutput(stdout,stderr)
                        flask.session['grouplist'] = eval(output)
                        return flask.redirect(flask.url_for('index'))
                else:
                        flask.flash(u'账号或密码错误 认证失败')
                        form.username_input.data = ''
                        form.psw_input.data = ''                        
                        return flask.redirect(flask.url_for('login'))
        return flask.render_template('login.html',form=form,head_message=u'请登录')
                
def checkUserInZabbix(username,passwd):
        try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect('10.139.39.196',22,'root','m2yMAg1r-',timeout=10)
                stdin,stdout,stderr = ssh.exec_command('python /opt/zabbixManaWeb/checkUserInZabbix.py %s %s'%(username,passwd))
                returnCode = checkOutput(stdout,stderr)
                #print returnCode
                if returnCode == 'True':
                        #ssh.exec_command('python /opt/zabbixManaWeb/getGroupsForUser.py %s %s'%(username,passwd))
                        
                        return (True,ssh)
                else:
                        return (False,None)
        except Exception,e:
                return False
def refreshInfo(username,passwd):
        try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect('10.139.39.196',22,'root','m2yMAg1r-')
                stdin,stdout,stderr = ssh.exec_command('python /opt/zabbixManaWeb/createUserConfig.py %s %s'%(username,passwd))
                returnCode = checkOutput(stdout,stderr)
                print returnCode
                if returnCode == 'True':
                        return True
                else:
                        return False
        except Exception,e:
                return False



###############################配置管理模块
@app.route('/configedit')
def configedit():
        return flask.render_template('config_edit.html',user=flask.session['username'],groups=flask.session.get('grouplist'))

@app.route('/hostlist')
def getHostlist():
        params = flask.request.args
        groupid = params.get('groupid')
        try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect('10.139.39.196',22,'root','m2yMAg1r-')
                stdin,stdout,stderr = ssh.exec_command('python /opt/zabbixManaWeb/getHostList.py %s'%(groupid))
                output = checkOutput(stdout,stderr)
        except Exception,e:
                output = "ERROR:"+str(e)
        return output

@app.route('/configedit/configcontent')
def getFileContent():
        params = flask.request.args
        ip = params.get('ip[]')
        try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip,22,'zabbix','Yp%rg7yS5',timeout=5)
                stdin,stdout,stderr = ssh.exec_command('cat /opt/zabbix/conf/zabbix_agent.userparams.conf')
                output = checkOutput(stdout,stderr)
        except Exception,e:
                output = "ERROR:"+str(e)
        return output

@app.route('/configedit/saveconfig',methods=['POST'])
def saveConfig():
        params = flask.request.form
        filecontent = params.get('filecontent').replace('\r\n','\n')
        try:
                ip = params.get('ip[]')
                tmpfile = open(filePath+'/upload_data/zabbix_agent.userparams.conf','wb+')
                tmpfile.write(filecontent)
                tmpfile.close()
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip,22,'zabbix','Yp%rg7yS5')
                ssh.exec_command('mv -f /opt/zabbix/conf/zabbix_agent.userparams.conf /opt/zabbix/conf/zabbix_agent.userparams.confbak')
                
                p = subprocess.Popen('python '+filePath+r'\scripts\putSomething.py %s %s %s'\
                %(r'zabbix_agent.userparams.conf',ip,'/opt/zabbix/conf/zabbix_agent.userparams.conf'),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                #print filecontent
                stdout,stderr = p.communicate()
                stdin,stdout,stderr = ssh.exec_command('sh /opt/zabbix/bin/zabbix.sh restart')
                output = checkOutput(stdout,stderr)
                if output == '':
                        return "修改成功!"
                else:
                        return output
        except Exception,e:
                return "ERROR:"+str(e)

@app.route('/startService',methods=['POST'])
def emergencyStartService():
        params = flask.request.form
        ip = params.get('ip[]')
        try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip,22,'zabbix','Yp%rg7yS5')
                stdin,stdout,stderr = ssh.exec_command('mv /opt/zabbix/conf/zabbix_agent.userparams.conf /opt/zabbix/conf/zabbix_agent.userparams.confbak1;mv /opt/zabbix/conf/zabbix_agent.userparams.confbak /opt/zabbix/conf/zabbix_agent.userparams.conf;sh /opt/zabbix/bin/zabbix.sh start')
                output = checkOutput(stdout,stderr)
                return output
        except Exception,e:
                return "ERROR:"+str(e)

@app.route('/configedit/batchEdit',methods=['POST'])
def batchEdit():
        params = flask.request.form
        iplist = params.get('iplist').split(',')
        method = params.get('method')
        content = params.get('content').replace("\r\n","\n")
        if params.get('iplist')=="" or content == "":
                return u"该主机组为空或未填写编辑内容!"
        if not re.search("^UserParameter=(.)+",content):
                return u"输入的参数不符合格式,正确格式应为每行一个参数，且为UserParameter=XXX的形式"
        overlapHosts = []
        errorHosts = {}
        successHosts = []
        threads = []
        lock = threading.Lock()
        for ip in iplist:
                try:
                        t = threading.Thread(target=batchEditOpe,args=(errorHosts,successHosts,overlapHosts,method,content,ip))
                        lock.acquire()
                        t.start()
                        threads.append(t)
                        lock.release()
                except Exception,e:
                        errorHosts[ip] = str(e)
                        #continue
        for thread in threads:
                thread.join()
        #print errorHosts
        if method == "ADD":
                if len(overlapHosts)==0 and len(errorHosts)==0:
                        return u" %s 添加成功!"%(repr(successHosts)[1:-1])
                elif len(overlapHosts)!=0 and len(errorHosts)==0:
                        return u" %s 等中有重复内容未添加!"%(repr(overlapHosts)[1:-1])
                elif len(errorHosts)!=0 and len(overlapHosts)==0:
                        return json.dumps(errorHosts)
                elif len(errorHosts)!=0 and len(overlapHosts)!=0:
                        for ip in overlapHosts:
                            errorHosts[ip] = u"内容重复 未添加"
                        return json.dumps(errorHosts)
        elif method == "DELETE":
                if len(overlapHosts)==0 and len(errorHosts)==0:
                        return u" %s 删除成功!"%(repr(successHosts)[1:-1])
                elif len(overlapHosts)!=0 and len(errorHosts)==0:
                        return u" %s 等中不存在部分要删除的内容，请单个编辑!"%(repr(overlapHosts)[1:-1])
                elif len(overlapHosts)==0 and len(errorHosts)!=0:
                        return json.dumps(errorHosts)
                elif len(overlapHosts)!=0 and len(errorHosts)!=0:
                        for ip in overlapHosts:
                            errorHosts[ip] = u"内容不存在 未删除"
                        return json.dumps(errorHosts)

def batchEditOpe(errorHosts,successHosts,overlapHosts,method,content,ip):
        flag = False
        try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip,22,'zabbix','Yp%rg7yS5')
                stdin,stdout,stderr = ssh.exec_command('cat /opt/zabbix/conf/zabbix_agent.userparams.conf')
                output = checkOutput(stdout,stderr)
                if "ERROR:" in output:
                    errorHosts[ip] = output
                    return 0
                userparams = output.strip().replace("\r","").split("\n")
        except Exception,e:
                errorHosts[ip] = str(e)
                return 0
        if method == "ADD":
                for para in userparams:
                        if para in content:
                                flag = True
                                break
                if flag == True:
                        overlapHosts.append(ip)
                        return 0
                tmpfile = open(filePath+'\upload_data\zabbix_agent.userparams.confat'+ip,"wb+")
                tmpfile.write(output.replace("\r","").strip())
                tmpfile.write("\n"+content)
                tmpfile.close()
        elif method == "DELETE":
                parasToDelete = content.split("\n")
                for para in parasToDelete:
                        if para not in userparams:
                                flag = True
                                break
                        else:
                                del(userparams[userparams.index(para)])
                if flag == True:
                        overlapHosts.append(ip)
                        return 0
                tmpfile = open(filePath+'\upload_data\zabbix_agent.userparams.confat'+ip,"wb+")
                for para in userparams:
                        tmpfile.write(para+'\n')
                tmpfile.close()
        stdin,stdout,stderr = ssh.exec_command('mv /opt/zabbix/conf/zabbix_agent.userparams.conf /opt/zabbix/conf/zabbix_agent.userparams.confbak')
        output = checkOutput(stdout,stderr)
        if "ERROR:" in output:
                errorHosts[ip] = output
                return 0
        p = subprocess.Popen('python '+filePath+'\scripts\putSomething.py %s %s %s'%\
                ('zabbix_agent.userparams.confat'+ip,ip,"/opt/zabbix/conf/zabbix_agent.userparams.conf"),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = p.communicate()
        output = checkOutput(stdout,stderr)
        if "ERROR:" in output :
                errorHosts[ip] = output
                p.kill()
                return 0
        stdin,stdout,stderr = ssh.exec_command('sh /opt/zabbix/bin/zabbix.sh restart')
        output = checkOutput(stdout,stderr)
        if "ERROR:" in output:
                errorHosts[ip] = output
                return 0
        successHosts.append(ip)
        




################################脚本管理模块#############################################
@app.route('/scriptmanagement')
def scriptManagement():
        return flask.render_template('script_manage.html',user=flask.session['username'],groups=flask.session.get('grouplist'))

@app.route('/scriptmanagement/scriptlist')
def getScriptList():
        params = flask.request.args
        ip = params.get('ip[]')
        try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip,22,'zabbix','Yp%rg7yS5',timeout=5)
                stdin,stdout,stderr = ssh.exec_command('for file in `ls /opt/zabbix/script/`;do echo $file;done')
                output = checkOutput(stdout,stderr)
                return output
        except Exception,e:
                return "ERROR:"+str(e)

@app.route('/scriptmanagement/addScript',methods=['GET','POST'])
def getAddScripts():
        if flask.request.form.get('filename')==None:
                cmd = 'dir /B '+filePath+r'\upload_data\add_script'
                p = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
                stdout,stderr = p.communicate()
                if stderr != '':
                        return "ERROR:"+stderr
                return stdout
        filename = flask.request.form.get('filename')
        ip = flask.request.form.get('ip')
        try:
                #print 'python '+filePath+r'\scripts\putSomething.py add_script/%s %s /opt/zabbix/script/%s'%(filename,ip,filename)
                p = subprocess.Popen('python '+filePath+'\scripts\putSomething.py %s %s %s'\
                %('add_script/'+filename,ip,'/opt/zabbix/script/'+filename),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                #print 'python '+filePath+'\scripts\putSomething.py %s %s %s'%('add_script/'+filename,ip,'/opt/zabbix/script/'+filename)
                stdout,stderr = p.communicate()
                output = checkOutput(stdout,stderr)
                if "ERROR:" in output:
                        return output
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip,22,'zabbix','Yp%rg7yS5')
                stdin,stdout,stderr = ssh.exec_command('chmod 755 /opt/zabbix/script/%s'%(filename))
                output = checkOutput(stdout,stderr)
                if "ERROR:" in output:
                        return output
                else:
                        return u"添加成功!"
        except Exception,e:
                return "ERROR:"+str(e)
@app.route('/scriptmanagement/deleteScript')
def deleteScript():
        params = flask.request.args
        ip = params.get('ip')
        filename = params.get('filename')
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip,22,'zabbix','Yp%rg7yS5',timeout=5)
        stdin,stdout,stderr = ssh.exec_command('rm -f /opt/zabbix/script/%s'%(filename))
        output = checkOutput(stdout,stderr)
        if output == '':
                return 'Success'
        else:
                return output
@app.route('/scriptmanagement/editScript')
def editScript():
        params = flask.request.args
        ip = params.get('ip')
        filename = params.get('filename')
        try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip,22,'zabbix','Yp%rg7yS5')
                stdin,stdout,stderr = ssh.exec_command('cat /opt/zabbix/script/%s'%(filename))
                output = checkOutput(stdout,stderr)
                if "ERROR:" in output:
                        return output
                else:
                        return json.dumps({'scriptcontent':output,'filename':filename})
                return output
        except Exception,e:
                return "ERROR:"+str(e)
        
@app.route('/scriptmanagement/saveScript',methods=['POST'])
def saveScript():
        params = flask.request.form
        try:
                scriptContent = params.get('scriptcontent').replace('\r\n','\n')
                filename = params.get('filename')
                ip = params.get('ip')
                scriptFile = open(filePath+r'/upload_data/%s'%(filename),'wb+')
                scriptFile.write(scriptContent)
                scriptFile.close()
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip,22,'zabbix','Yp%rg7yS5')
                p = subprocess.Popen('python '+filePath+'/scripts/putSomething.py %s %s %s'\
        %(filename,ip,'/opt/zabbix/script/%s'%(filename)),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                stdout,stderr = p.communicate()
                if stderr != '':
                        return "ERROR:"+stderr
                stdin,stdout,stderr = ssh.exec_command('chmod 755 /opt/zabbix/script/%s'%(filename))
                output = checkOutput(stdout,stderr)
                if output == '':
                        return '修改成功！'
                else:
                        return output
        except Exception,e:
                return "ERROR:"+str(e)

@app.route('/scriptmanagement/batchAddScript',methods=['POST'])
def batchAddScript():
        param = flask.request.form
        filename = param.get('filename')
        iplist = param.get('iplist').split(',')
        if param.get('iplist') == "":
                return u"选择主机组为空!"
        errorHosts = {}
        successHosts = []
        threads = []
        lock = threading.Lock()
        for ip in iplist:
                try:
                        t = threading.Thread(target=batchAddScriptOpe,args=(errorHosts,successHosts,ip,filename))
                        lock.acquire()
                        t.start()
                        threads.append(t)
                        lock.release()
                except Exception,e:
                        errorHosts[ip] = str(e)
        for thread in threads:
                thread.join()
        #print errorHosts
        if len(errorHosts)==0:
                return u" %s 添加脚本%s成功"%(repr(successHosts)[1:-1],filename)
        else:
                return json.dumps(errorHosts)

def batchAddScriptOpe(errorHosts,successHosts,ip,filename):
        p = subprocess.Popen('python '+filePath+'\scripts\putSomething.py %s %s %s'\
        %('add_script/'+filename,ip,'/opt/zabbix/script/'+filename),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        #print 'python '+filePath+'\scripts\putSomething.py %s %s %s'%('add_script/'+filename,ip,'/opt/zabbix/scripts/'+filename)
        stdout,stderr = p.communicate()
        output = checkOutput(stdout,stderr)
        if "ERROR:" in output:
                errorHosts[ip] = output
                p.kill()
                return 0
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip,22,'zabbix','Yp%rg7yS5',timeout=1)
        stdin,stdout,stderr = ssh.exec_command('chmod 755 /opt/zabbix/script/%s'%(filename))
        output = checkOutput(stdout,stderr)
        if "ERROR:" in output:
                return output
        else:
                successHosts.append(ip)
        

@app.route('/exit')
def exit():
        flask.session['username'] = None
        return flask.redirect(flask.url_for('login'))
        
if __name__ == "__main__":
        app.run(debug=True,host='0.0.0.0',port=5001,threaded=True)
