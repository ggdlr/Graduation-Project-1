from flask import Flask, g, render_template, Markup, redirect, request, url_for, session, make_response, jsonify
import requests, json
import paramiko
import pymysql
import time

url = 'http://192.168.0.96:8080/client/api'
ubuntugcc='abdb7db1-8857-47fb-bd19-2671fdc4da90'
ubuntupython='093db850-44f2-473e-933d-a06b76370815'
centosgcc='0663ec39-58ea-4bda-a79d-3ed8e2223435'
centospython='627aabe4-f263-4339-aafc-925b26f5a535'

smallcpu = '3174c21a-760e-4f79-bc1f-76bfd20ca5b4'
mediumcpu = '7a74b0d9-ebdd-42b3-a1e4-80be06c0433f'

smalldisk = 'bcfd66c6-2431-40f4-9d49-a74ad4283d61'
mediumdisk = '35fae8c2-d628-4b1d-b110-0218e09a7e18'
largedisk = '7ba43e5e-709b-4826-bf2a-f76987ad725b'

username = ''
app = Flask(__name__)
# app.jinja_env.trim.blocks = True
status = 0
def getLoginStatus(username,password):
    login_data = {'command':'login', 'username':username, 'password': password, 'response':'json'}
    global user
    user = requests.Session()
    req = user.post(url, data=login_data)
    global status
    status = req.status_code
    return status
def logout():
    logout_data = {'command': 'logout'}
    global user
    req3 = user.post(url,data=logout_data)
    if(req3.status_code == 200):
        global status
        status = 0
        return redirect(url_for('mainDisplay'))
    else: return 'Something went wrong. Log out failed'
def adminLogin(username,password):
    login_data = {'command':'login', 'username':username, 'password': password, 'response':'json'}
    global admin
    admin = requests.Session()
    req = admin.post(url, data=login_data)

def CreateUser(email,firstname,lastname,password,username):
    createuser_data = {'command':'createUser','account':'admin','email':email,'firstname': firstname, 'lastname': lastname, 'username':username, 'password': password, 'response': 'json'}

    req1 = admin.post(url, data=createuser_data)
    
    global status
    status = req1.status_code
    if(status == 200):
        return getLoginStatus(username,password)
    return req1.status_code

def deploy(template,diskid,cpu):
    deploy_vm_data = {'command': 'deployVirtualMachine', 'serviceofferingid' : cpu,'templateid': template,'zoneid':'18834e25-c1c7-4676-bbf6-08028d2d8d6f', ' diskofferingid':diskid,'response':'json'}
    global user
    req_dep_vm = user.post(url,data=deploy_vm_data)
    resp = req_dep_vm.json()
    res1 = resp['deployvirtualmachineresponse']
    res2 = res1 ['id']
    return res2

def getVMIp(vm_id):
    vm_data = {'command': 'listVirtualMachines', 'id' : vm_id,'response':'json'}
    global user
    req_vm = user.post(url,data=vm_data)
    resp = req_vm.json()
    res = resp['listvirtualmachinesresponse']
    res1 = res['virtualmachine']
    res2 = res1[0]
    res3 = res2['nic']
    res4 = res3[0]
    res5 = res4['ipaddress']
    return res5

def expungeVm(vm_id):
    expunge_data = {'command': 'destroyVirtualMachine', 'id' : vm_id, 'expunge':'true', 'response':'json'}
    global user
    req_expunge_vm = user.post(url,data=expunge_data)
    return req_expunge_vm.status_code

class Ssh:
    Shell = None
    client = None
    transport = None
    ftp = None
    flag = False
    def __init__(self, address, username, password):
        print("Connecting to server on ip", str(address) + ".")
        self.client = paramiko.client.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        # self.client.connect(address, username=username, password=password)
        # self.transport = paramiko.Transport((address, 22))
        # self.transport.connect(username=username, password=password)
        # self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        try:
            self.client.connect(address, username=username, password=password)
            self.transport = paramiko.Transport((address, 22))
            self.transport.connect(username=username, password=password)
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)  
            self.flag = True
        except Exception as e:
            self.flag = False

    def close_connection(self):
        try:
            self.client.close()
            self.sftp.close()
            self.transport.close()
        except Exception as e:
            print(str(e))

    def open_shell(self):
        try:
            self.Shell = self.client.invoke_shell()
        except Exception as e:
            print(str(e))

    def mv_dir(self, path):
        try:
            self.Shell.send("cd " + path + "\n")
        except Exception as e:
            print(str(e))

    def put_file(self, lpath, rpath, file_name):
        try:
            local_path = lpath + '/' + file_name
            remote_path = rpath + '/' + file_name
            self.sftp.put(remote_path, local_path)
        except Exception as e:
            print(str(e))

    def get_file(self, lpath, rpath, file_name):
        try:
            local_path = lpath + '/' + file_name
            remote_path = rpath + '/' + file_name
            self.sftp.get(remote_path, local_path)
        except Exception as e:
            print(str(e))

    def f_write(self, path, file_name, contents):
        try:
            ftp = self.sftp.open(path + '/' + file_name, "w")
            ftp.write(contents)
            ftp.flush()
            ftp.close()
        except Exception as e:
            print(str(e))

    def mkfile(self, path, file_name):
        try:
            self.Shell.send("cd " + path + '\n')
            self.Shell.send("touch " + file_name + "\n")
        except Exception as e:
            print(str(e))

    def chfname(self, path, oldname, newname):
        try:
            self.Shell.send("cd " + path + '\n')
            self.Shell.send("mv " + oldname + ' ' + newname + '\n')
        except Exception as e:
            print(str(e))

    def rmfile(self, path, file_name):
            try:
                self.Shell.send("cd " + path + '\n')
                self.Shell.send("rm -rf " + file_name + "\n")
            except Exception as e:
                print(str(e))

    def show_code(self, path, file_name):
        try:
            ftp = self.sftp.open(path + '/' + file_name, 'r')
            result = ftp.read()
            ftp.flush()
            ftp.close()
        except Exception as e:
            print(str(e))

    def run_cfile(self, file_name):
        try:
            self.Shell.send("gcc " + file_name + " -o " + file_name + ".out\n")
            self.Shell.send("./" + file_name + ".out\n")
        except Exception as e:
            print(str(e))

    def run_pyfile(self, file_name):
        try:
            self.Shell.send("python3 " + file_name + "\n")
        except Exception as e:
            print(str(e))

    def send_command(self, command):
        try:
            self.Shell.send(command + '\n')
        except Exception as e:
            print(str(e))

    def print_result(self):
        try:
            output = self.Shell.recv(65535).decode("utf-8")
            return output
        except Exception as e:
            print(str(e))
sshServer = ""
ubuntuser = "root"
ubuntupw = "123456"
centosuser = "root"
centospw = "123456"
# connection = Ssh(sshServer, sshUsername, sshPassword)
# connection.open_shell()
db = pymysql.connect(host='192.168.0.96', user='root', passwd='', db='user_info', charset='utf8')
cursor = db.cursor()

@app.route('/',methods = ['GET','POST'])
def mainDisplay():
    adminLogin('admin','123456')
    global username
    # if (request.method == 'POST'):
    #     if ('register' in request.form):
    #         return redirect(url_for('registerPage'))
    #     elif ('login' in request.form):
    #         global username
    #         username = request.form['username']
    #         password= request.form['password']
    #         if(getLoginStatus(username,password)==200):
    #             return redirect(url_for('infoPage'))
    #     else: 
    #         return 'Something went wrong, please try again'
    if(username == '' or username == None):
        return render_template('login.html')
    else:
        return render_template('afterlogin.html', username = username)

@app.route('/afterlogin', methods=['GET', 'POST'])
def afterlogin():   
    global username
    username = request.form['username']
    password= request.form['password']
    if(getLoginStatus(username,password)==200):
        return render_template('afterlogin.html', username = username)
    else: 
        return render_template('login.html')

@app.route('/inviteinfo', methods = (['GET', 'POST']))
def inviteinfoPage():
    i = 0
    global username
    fromid=[]
    teamid=[]
    sql = '''
                SELECT from_id, team_id FROM invite where to_id = %s
        '''
    cursor.execute(sql, username)
    result = cursor.fetchall()
    for tup in result:
        fromid.insert(i, tup[0])
        teamid.insert(i, tup[1])
        i = i + 1
    invitelen=len()
    return render_template('afterlogin.html', fromid=fromid, teamid=teamid)

@app.route('/register', methods = (['GET', 'POST']))
def registerPage():
    global username
    if request.method == 'POST': 
        email = request.form['email']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        username = request.form['username']
        password= request.form['password']
        if(CreateUser(email,firstname,lastname,password,username)==200 ):
            return render_template('afterlogin.html', username = username)
        else:
            return 'Something went wrong. Try to register again'
    return render_template('register.html')

@app.route('/aftercreate', methods = (['GET', 'POST']))
def aftercreate():
    disk = request.form['disk']
    cpu = request.form['cpu']
    os = request.form['os']
    language = request.form['language']
    diskid=''
    cpuid=''
    template=''

    if disk =='small':
        diskid = smalldisk
    elif disk =='medium':
        diskid = mediumdisk
    elif disk == 'large':
        diskid = largedisk

    if cpu =='small':
        cpuid = smallcpu
    elif cpu=='medium':
        cpuid = mediumcpu

    if os == 'centos' and language =='ccpp':
        template=centosgcc
    elif os == 'ubuntu' and language =='ccpp':
        template=ubuntugcc
    elif os == 'centos' and language =='python':
        template=centospython
    elif os == 'ubuntu' and language =='python':
        template=ubuntupython

    vmid=deploy(template,diskid,cpuid)
    global username    
    u_id = username
    
    sql1 = '''
            INSERT INTO vm_info (user_id, os, lang, vm_id, vm_disk, vm_cpu) VALUES (%s, %s, %s, %s, %s, %s)'''
    cursor.execute(sql1, (u_id, os, language, vmid, disk, cpu))
    db.commit()
    
    return redirect(url_for('infoPage'))

@app.route('/info', methods = (['GET','POST']))
def infoPage():
    # if('logout' in request.form):
    #     return logout()
    # elif (status!=200):
    #     return 'Error. You are not logged in'
    global username
    i = 0
    u_os = []
    u_lang = []
    u_vm = []
    u_vmid = []
    sql2 = '''
            SELECT user_id, os, lang, vm_ip, vm_id FROM vm_info where user_id = %s
        '''
    cursor.execute(sql2, username)
    result = cursor.fetchall()
    for tup in result:
        if tup[0] == username:
            u_os.insert(i, tup[1])
            u_lang.insert(i, tup[2])
            u_vm.insert(i,tup[3])
            u_vmid.insert(i,tup[4])
            i = i + 1
    #db.close()
    result_len = len(result)
    return render_template('info.html', u_id=username, os=u_os, language=u_lang, len=result_len, vm_ip = u_vm, vm_id=u_vmid)

@app.route('/getip', methods = (['GET','POST']))
def getip():
    vmid = request.form['vm_id']
    #global vm_ip
    vm_ip = getVMIp(vmid)
    sql = '''
                UPDATE vm_info SET vm_ip = %s WHERE vm_id = %s '''
    cursor.execute(sql, (vm_ip, vmid))
    db.commit()
    return jsonify(result = vm_ip)
@app.route('/create', methods = (['GET', 'POST']))
def createPage():
    if(request.method == 'POST'):
        if('logout' in request.form):
            return logout()
    if (status==200):
        return render_template('create.html')
    else: return 'Error. You are not logged in'

@app.route('/teamlist', methods = ['GET', 'POST'])
def teamlist():
    i = 0
    global username
    teamlist=[]
    sql = '''
                SELECT team_id FROM team_users where user_id = %s       
            '''                                                                 #select team id 
    cursor.execute(sql, username)
    result = cursor.fetchall()
    for tup in result:
        teamlist.insert(i,tup[0])
        i = i + 1
    return render_template('teamlist.html', uername = username)

@app.route('/team', methods = ['GET', 'POST'])
def teamPage():
    global username
    global teamid
    teamid = 7
    teamid = 9
    userlist = []
    postlist = []
    vmlist = []
    i = 0
    sql = '''
                SELECT user_id FROM team_users where team_id = %s       
            '''                                                                 #select user id in team
    cursor.execute(sql, teamid)
    result = cursor.fetchall()
    for tup in result:
        userlist.insert(i,tup[0])
        i = i + 1
    i = 0
    sql2 = '''
                    SELECT contents FROM post where team_id = %s
                '''                                                         #select post in team
    cursor.execute(sql2, teamid)
    result2 = cursor.fetchall()
    for tup in result2:
        postlist.insert(i, tup[0])
        i = i + 1
    i = 0
    sql3 = '''
                    SELECT vm_ip FROM teamvminfo where team_id = %s
                '''                                                          #select vmip in team
    cursor.execute(sql3, teamid)
    result = cursor.fetchall()
    for tup in result:
        vmlist.insert(i,tup[0])
        i = i + 1

    if('logout' in request.form):
        return logout()
    if ("create" in request.form):
        return render_template('teamcreate.html')
    if ("adduser" in request.form):
        return redirect(url_for('adduserPage'))
    if ("post" in request.form):
        return redirect(url_for('addpostPage'))
    vmlistlen=len(vmlist)
    return render_template('team.html',userlist=userlist, postlist=postlist, vmlist=vmlist, len=vmlistlen)

@app.route('/addpost', methods=['GET','POST'])        #add post to db('post' table)
def addpostPage():
    sql = '''
            INSERT INTO post (team_id, contents) VALUES (%s, %s)
        '''
    cursor.execute(sql, (teamid, contents))  
    db.commit()     
    return redirect(url_for('teamPage'))

@app.route('/adduser', methods=['GET','POST'])            #add user to db('team users'table)
def adduserPage():
    global teamid
    user_id = request.form['username']
    sql1 = '''
            INSERT INTO team_users (team_id, user_id) VALUES (%s, %s)'''
    cursor.execute(sql1, (teamid, user_id))
    db.commit() 
    return redirect(url_for('teamPage')) 

@app.route('/afterteamcreate', methods=['GET','POST'])          #add vm information to db(teavminfo table)
def afterteamcreate():
    global teamid
    cpu = request.form['cpu']
    disk = request.form['disk']
    os = request.form['os']
    language = request.form['language']
    template = ''
    diskid = ''
    cpuid = ''

    if disk =='small':
        diskid = smalldisk
    elif disk =='medium':
        diskid = mediumdisk
    elif disk == 'large':
        diskid = largedisk

    if cpu =='small':
        cpuid = smallcpu
    elif cpu=='medium':
        cpuid = mediumcpu

    if os == 'centos' and language =='ccpp':
        template=centosgcc
    elif os == 'ubuntu' and language =='ccpp':
        template=ubuntugcc
    elif os == 'centos' and language =='python':
        template=centospython
    elif os == 'ubuntu' and language =='python':
        template=ubuntupython

    vmid=deploy(template,diskid,cpuid) 
    sql1 = '''
            INSERT INTO teamvminfo (team_id, vm_id, vm_os, vm_lang, vm_disk, vm_cpu) VALUES (%s, %s, %s, %s, %s, %s)'''
    cursor.execute(sql1, (teamid, vmid, os, language, disk, cpu))
    db.commit()         
    return redirect(url_for('teamPage'))


@app.route('/editor', methods = ['GET','POST'])
def editorPage():
    j = 0
    global username
    # if (username =='' or username == None):
    #     return "You are not logged in"
    u_id = username
    idlist=[]
    if ("delete" in request.form):
        idx=request.form['vm']
        sql = '''
                SELECT vm_id FROM vm_info where user_id = %s
            '''
        cursor.execute(sql, u_id)
        result3 = cursor.fetchall()
        for tup in result3:
            idlist.insert(j,tup[0])
            j = j + 1
        deleteid=idlist[int(idx)]
        sql1 = '''
                DELETE FROM vm_info WHERE vm_id = %s
            '''
        cursor.execute(sql1, deleteid)
        db.commit()
        expungeVm(deleteid)
        return redirect(url_for('infoPage'))

    elif("start" in request.form):
        idx=request.form['vm']
        i=0
        global vlang
        global vos
        global code_result
        global code
        global vip
        u_id = username
        u_os=[]
        u_vm =[]
        u_lang=[]
        flist=[]
        code_result = ''
        code = ''
        
        sql = '''
                SELECT os, lang, vm_ip FROM vm_info where user_id = %s
            '''
        cursor.execute(sql, u_id)
        result = cursor.fetchall()
        for tup in result:
            u_os.insert(i, tup[0])
            u_lang.insert(i,tup[1])
            u_vm.insert(i,tup[2])
            i = i + 1
        vip = u_vm[int(idx)]
        vos = u_os[int(idx)] 
        vlang = u_lang[int(idx)]
        if vos == 'ubuntu':
            user = ubuntuser
            pw = ubuntupw
        elif vos == 'centos':
            user = centosuser
            pw = centospw  
        global connection
        connection = Ssh(vip, user, pw)

        print(connection.flag)
        if connection.flag == False:
            return redirect(url_for('infoPage'))
        connection.open_shell()
        sql1 = '''
                SELECT fname FROM user_code where user_id = %s and vm_ip = %s
            '''
        cursor.execute(sql1, (u_id,vip))
        result1 = cursor.fetchall()
        for tup in result1:
            flist.insert(j,tup[0])
            j = j + 1
        flen=len(flist)
        # if('logout' in request.form):
        #     return logout()
        # if (status!=200):
        #     return 'Error. You are not logged in'
        # else:
        return render_template('editor.html',uid=username, files=flist, flen=flen)
    elif("create" in request.form):
        return redirect(url_for('createPage'))
    elif('logout' in request.form):
        return logout()
    elif (status!=200):
        return 'Error. You are not logged in'
    


@app.route('/runcode', methods=['GET', 'POST'])
def runcode():
    global code_result
    global code
    code_result = ''
    code=''
    fname = request.form['filename']
    code = request.form['code']
    connection.f_write('/home', fname, code)
    connection.send_command('cd /home')
    if vlang=='ccpp':
        connection.rmfile('/home',fname+'.out')
        drop=connection.print_result()
        connection.run_cfile(fname)
        time.sleep(1)
        code_result = connection.print_result()
    elif vlang =='python':
        connection.print_result()
        drop=connection.run_pyfile(fname)
        time.sleep(1)
        code_result = connection.print_result()
    # connection.close_connection()
    sql = '''
            UPDATE user_code SET code = %s WHERE fname = %s '''
    cursor.execute(sql, (code, fname))
    db.commit()
    return jsonify(result = code_result)

@app.route('/showcode', methods=['GET', 'POST'])
def showcode():
    fname = request.form['filename']
    sql = '''
            SELECT code FROM user_code WHERE fname = %s '''
    cursor.execute(sql, fname)
    result = cursor.fetchall()
    return jsonify(result = result)

@app.route('/addfile', methods=['GET', 'POST'])
def addfile():
    global username
    global connection
    global vip
    uid = username
    flist=[]
    j=0
    fname = request.form['filename']

    sql2 = '''
            SELECT fname FROM user_code WHERE user_id = %s and vm_ip = %s'''
    cursor.execute(sql2,(username,vip))
    result=cursor.fetchall()
    for tup in result:
        flist.insert(j,tup[0])
        j = j + 1
    if fname in flist:
        canCreate = 0
    else:
        canCreate = 1
        sql = '''
                        INSERT INTO user_code (fname, user_id, vm_ip) VALUES (%s, %s, %s)'''
        cursor.execute(sql, (fname, uid,vip))
        db.commit()
        connection.mkfile('/home', fname)
        connection.print_result()
    return jsonify(canCreate = canCreate)

@app.route('/renamefile', methods=['GET', 'POST'])
def renamefile():
    global username
    global vip
    uid = username
    fname = request.form['filename']
    newname = request.form['newname']
    j=0
    flist=[]
    sql2 = '''
                SELECT fname FROM user_code WHERE user_id = %s and vm_ip = %s '''
    cursor.execute(sql2,(username,vip))
    result=cursor.fetchall()
    for tup in result:
        flist.insert(j,tup[0])
        j = j + 1
    if newname in flist:
        canCreate = 0
    else:
        canCreate = 1
        sql = '''
                        UPDATE user_code SET fname = %s WHERE fname = %s and vm_ip = %s'''
        cursor.execute(sql, (newname, fname, vip))
        db.commit()
        connection.chfname('/home', fname, newname)
        connection.print_result()
    return jsonify(canCreate = canCreate)

@app.route('/removefile', methods=['GET', 'POST'])
def removefile():
    global username
    global vip
    uid = username
    fname = request.form['filename']
    sql = '''
                    DELETE FROM user_code WHERE fname = %s  and vm_ip = %s '''
    cursor.execute(sql, (fname,vip))
    db.commit()
    connection.rmfile('/home', fname)
    connection.print_result()
    return jsonify()

if(__name__)=='__main__':
    app.run(host='0.0.0.0', debug=True)
# @app.before_request

# def before_request():
#     print("before_request")
#     g.str = "한글"

# @app.route("/tmpl")
# def t():
#     tit = Markup("<strong>Title<strong>")
#     mu = Markup("<h1>iii = <i>%s</i></h1>")
#     h = mu % "Italic"
#     print("h=", h)
#     return render_template('index.html', title = tit, mu = h)

# @app.route("/")
# def helloworld():
#     return "Hello Flask World!"

# @app.route("/gg")
# def helloworld2():
#     return "Hello Flask World!" + getattr(g, 'str', '111')


