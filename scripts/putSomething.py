#! /usr/bin/env python
#coding=utf-8
import paramiko,sys,os
filePath = os.path.dirname(__file__)
filePath = os.path.dirname(filePath)

def main():
	filename = sys.argv[1]
	remote_ip = sys.argv[2]
	to_path = sys.argv[3]
	##########################
	#to_path必须是绝对路径且带上文件名，paramiko自动覆盖重名文件
	##########################
	try:
		#print r'######################%s\upload_data\%s'%(filePath,filename)
		#print os.path.isfile(r'%s\upload_data\%s'%(filePath,filename))
		if not os.path.exists(r'%s\upload_data\%s'%(filePath,filename)):
			raise Exception('No File %s in upload_data'%(filename))
		tra = paramiko.Transport((remote_ip,22))
		tra.connect(username='zabbix',password='Yp%rg7yS5')
		sftp = paramiko.SFTPClient.from_transport(tra)
		sftp.put('%s/upload_data/%s'%(filePath,filename),to_path)
		#print '%s/upload_data/%s'%(filePath,filename)
		tra.close()
	except Exception,e:
		raise
		print str(e)
if __name__ == '__main__':
	main()
