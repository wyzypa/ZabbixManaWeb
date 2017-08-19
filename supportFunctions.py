def checkOutput(stdout,stderr):
        if isinstance(stdout,str) or isinstance(stderr,str):
                errmsg = stderr
                outmsg = stdout
        else:
                errmsg = stderr.read()
                outmsg = stdout.read()
        if errmsg != '' and errmsg != None:
                return "ERROR:"+errmsg
        else:
                return outmsg