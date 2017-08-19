import paramiko,sys,os
filePath = os.path.dirname(__file__)
filePath = os.path.dirname(filePath)

def check_output(stderr,stdout):
	errmsg = stderr.read()
	outmsg = stdout.read()
	if errmsg != '':
		return errmsg
	else:
		return outmsg
def main():
	ip = sys.argv[1]
	target = sys.argv[2]
	real_target = '/'+target.strip('/').split('/')[-1]+'/'
	print real_target
	if target[-1]!='/':
		pattern = 'FILE'
	else:
		pattern = 'DIRECTORY'
	try:
		tra = paramiko.Transport((ip,22))
		tra.connect(username='zabbix',password='Yp%rg7yS5')
		sftp = paramiko.SFTPClient.from_transport(tra)
		if pattern == 'FILE':
			print 'START DOWNLOADING...'
			sftp.get(target,filePath+"\\download_data\\"+os.path.basename(target))
			print 'OVER!'
		elif pattern == 'DIRECTORY':
			ssh = paramiko.SSHClient()
			ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			ssh.connect(ip,22,'zabbix','Yp%rg7yS5')
			cmd = 'find %s -type f | wc -l'%(target)
			stdin,stdout,stderr = ssh.exec_command(cmd)
			fileTotalCount = int(check_output(stderr,stdout))
			
			cmd = 'echo -e "import os\nfor item in os.walk(\'%s\'):\n\tprint item" | python' % (target[:-1])
			stdin,stdout,stderr = ssh.exec_command(cmd)
			output = check_output(stderr,stdout)
			dirsstr = output.split('\n')
			count = 0
			for dirstr in dirsstr:
				if dirstr == '':
					continue
				dir =  eval(dirstr)
				index = dir[0].find(real_target)
				if index == -1:
					real_dir = real_target[:-1]
				else:
					real_dir = dir[0][index:]
				os.makedirs('%s\download_data%s'%(filePath,real_dir))
				#continue
				for file in dir[2]:
					filename = dir[0]+'/'+file
					real_filename = real_dir+'/'+file
					count += 1
					print 'downloading %s ..... || %.0f%% completed!' % (filename,float(count)/fileTotalCount*100)
					sftp.get(filename,'%s\download_data%s'%(filePath,real_filename))
		tra.close()
	except Exception,e:
		raise
		print str(e)

if __name__ == '__main__':
	main()
