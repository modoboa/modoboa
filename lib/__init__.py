# -*- coding: utf-8 -*-
import popen2
import os
import time
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response

def exec_pipe(cmd):
    """Exécute une commande et récupère la sortie générée

    Le module popen2 est utilisé pour l'exécution de la commande. Un
    objet Popen4 est créé car il regroupe la sortie standard et la sortie
    d'erreur dans le même fd.
    De plus, popen2 est le seul à pouvoir capturer retourner le code de
    sortie de la commande.

    cmd -- commande à exécuter

    Retourne un couple (code de sortie, texte de sortie)
    """
    child = popen2.Popen4(cmd)
    child.tochild.close()
    while True:
        ret = child.poll()
        if ret != -1:
            break
        time.sleep(0.001)
    output = child.fromchild.read()
    if not ret:
        code = 0
    else:
        if os.WIFEXITED(ret):
            code = os.WEXITSTATUS(ret), output
        else:
            code = -1
    return code, output

def crypt_password(raw_password):
    import md5
    import random

    salt = md5.new(str(random.random) + str(random.random)).hexdigest()
    salt = salt[:5]
    hash = md5.new(salt + raw_password).hexdigest()
    return "%s$%s$%s" % ("md5", salt, hash)

def _render(request, tpl, user_context):
    return render_to_response(tpl, user_context, 
                              context_instance=RequestContext(request))

def exec_as_vuser(cmd):
    code, output = exec_pipe("sudo -u %s %s" % (settings.VIRTUAL_UID, cmd))
    if code:
        os.system("echo '%s' >> /tmp/vmail.log" % output)
        return False
    return True
