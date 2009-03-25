# -*- coding: utf-8 -*-
import popen2
import os
import time
from django.conf import settings

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


def create_domain(name):
    code, output = exec_pipe("sudo -u %s mkdir %s/%s" \
                                 % (settings.VIRTUAL_UID, settings.STORAGE_PATH, 
                                    name))
    if code:
        os.system("echo '%s' >> /tmp/vmail.log" % output)
        return False
    return True

def destroy_domain(name):
    code, output = exec_pipe("sudo -u %s rm -r %s/%s" \
                                 % (settings.VIRTUAL_UID, settings.STORAGE_PATH, 
                                    name))
    if code:
        return False
    return True

def create_mailbox(domain, name):
    code, output = exec_pipe("sudo -u %s mkdir -p %s/%s/%s/.maildir" \
                                 % (settings.VIRTUAL_UID, settings.STORAGE_PATH,
                                    domain, name))
    if code:
        return False
    return True

def destroy_mailbox(domain, name):
    code, output = exec_pipe("sudo -u %s rm -r %s/%s/%s" \
                                 % (settings.VIRTUAL_UID, settings.STORAGE_PATH,
                                    domain, name))
    if code:
        return False
    return True
