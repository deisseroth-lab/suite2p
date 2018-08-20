from PyQt5 import QtGui, QtCore
import sys
import numpy as np
from scipy.ndimage import gaussian_filter
import os
from sklearn.linear_model  import LogisticRegression
from suite2p import fig, gui
import time

class Classifier:
    def __init__(self, classfile=None):
        # stat are cell stats from currently loaded recording
        # classfile is a previously saved classifier file
        if classfile is not None:
            self.classfile = classfile
            self.load()
        else:
            self.loaded = False

    def load(self):
        try:
            model = np.load(self.classfile)
            model = model.item()
            self.stats = model['stats']
            self.iscell = model['iscell']
            self.keys = model['keys']
            self.loaded = True
        except (ValueError, KeyError, OSError, RuntimeError, TypeError, NameError):
            print('ERROR: incorrect classifier file')
            self.loaded = False

    def apply(self, stat):
        y_pred     = probability(stat,self.stats,self.iscell,self.keys)
        return y_pred

def get_logp(test_stats, grid, p):
    nroi, nstats = test_stats.shape
    logp = np.zeros((nroi,nstats))
    for n in range(nstats):
        x = test_stats[:,n]
        x[x<grid[0,n]]   = grid[0,n]
        x[x>grid[-1,n]]  = grid[-1,n]
        ibin = np.digitize(x, grid[:,n], right=True) - 1
        logp[:,n] = np.log(p[ibin,n] + 1e-6) - np.log(1-p[ibin,n] + 1e-6)
    return logp

def probability(stat, train_stats, train_iscell, keys):
    nodes = 100
    nroi, nstats = train_stats.shape
    ssort= np.sort(train_stats, axis=0)
    isort= np.argsort(train_stats, axis=0)
    ix = np.linspace(0, nroi-1, nodes).astype('int32')
    grid = ssort[ix, :]
    p = np.zeros((nodes-1,nstats))
    for j in range(nodes-1):
        for k in range(nstats):
            p[j, k] = np.mean(iscell[isort[ix[j]:ix[j+1], k]])
    p = gaussian_filter(p, (2., 0))
    logp = self.get_logp(train_stats, grid, p)
    logisticRegr = LogisticRegression(C = 100.)
    logisticRegr.fit(logp, iscell)
    # now get logP from the test data
    test_stats = get_stat_keys(stat, keys)
    logp = get_logp(test_stats, grid, p)
    y_pred = logisticRegr.predict_proba(logp)
    y_pred = y_pred[:,1]
    return y_pred

def get_stat_keys(stat, keys):
    test_stats = np.zeros((len(stat), len(keys)))
    for j in range(len(stat)):
        for k in range(len(keys)):
            test_stats[j,k] = stat[j][keys[k]]
    return test_stats

def run(classfile,stat):
    model = Classifier(classfile=classfile)
    # compute cell probability
    probcell = model.apply(stat)
    iscell = probcell > 0.5
    iscell = np.concatenate((np.expand_dims(iscell,axis=1),np.expand_dims(probcell,axis=1)),axis=1)
    return iscell

def load(parent, name):
    print('loading classifier ', name)
    parent.model = Classifier(classfile=name)
    if parent.model.loaded:
        activate(parent, True)

def load_list(parent):
    # will return
    LC = gui.ListChooser('classifier training files', parent)
    result = LC.exec_()
    if result:
        print('Populating classifier:')
        model = Classifier(classfile=parent.classfile)
        keys = model.keys
        parent.model = Classifier(classfile=None,
                                           trainfiles=parent.trainfiles,
                                           statclass=parent.statclass)
        if parent.trainfiles is not None:
            activate(parent, True)

def load_data(keys,trainfiles):
    train_stats = np.zeros((0,len(keys)),np.float32)
    train_iscell = np.zeros((0,),np.float32)
    trainfiles_good = []
    if trainfiles is not None:
        for fname in trainfiles:
            badfile = False
            basename, bname = os.path.split(fname)
            try:
                iscells = np.load(fname)
                ncells = iscells.shape[0]
            except (ValueError, OSError, RuntimeError, TypeError, NameError):
                print('\t'+fname+': not a numpy array of booleans')
                badfile = True
            if not badfile:
                basename, bname = os.path.split(fname)
                lstat = 0
                try:
                    stat = np.load(basename+'/stat.npy')
                    ypix = stat[0]['ypix']
                    lstat = len(stat)
                except (KeyError, OSError, RuntimeError, TypeError, NameError):
                    print('\t'+basename+': incorrect or missing stat.npy file :(')
                if lstat != ncells:
                    print('\t'+basename+': stat.npy is not the same length as iscell.npy')
                else:
                    # add iscell and stat to classifier
                    print('\t'+fname+' was added to classifier')
                    iscell = iscells[:,0].astype(np.float32)
                    nall = get_stat_keys(stat,keys)
                    train_stats = np.concatenate((train_stats,nall),axis=0)
                    train_iscell = np.concatenate((train_iscell,iscell),axis=0)
                    trainfiles_good.append(fname)
    if len(trainfiles_good) > 0:
        save(parent,train_stats,train_iscell,keys)


def apply(parent):
    classval = parent.probedit.value()
    iscell = parent.probcell > classval
    fig.flip_for_class(parent, iscell)
    M = fig.draw_masks(parent)
    fig.plot_masks(parent,M)
    np.save(parent.basename+'/iscell.npy',
            np.concatenate((np.expand_dims(parent.iscell,axis=1),
            np.expand_dims(parent.probcell,axis=1)), axis=1))
    parent.lcell0.setText(' %d'%parent.iscell.sum())
    parent.lcell1.setText(' %d'%(parent.iscell.size-parent.iscell.sum()))

def save(parent, train_stats, train_iscell, keys):
    name = QtGui.QFileDialog.getSaveFileName(parent,'Save classifier')
    if name:
        try:
            model = {}
            model['stats']  = train_stats
            model['iscell'] = train_iscell
            model['keys']   = keys
            print('saving classifier in ' + fname)
            np.save(fname, model)
        except (OSError, RuntimeError, TypeError, NameError,FileNotFoundError):
            print('ERROR: incorrect filename for saving')

def save_list(parent):
    name = QtGui.QFileDialog.getSaveFileName(parent,'Save list of iscell.npy')
    if name:
        try:
            with open(name[0],'w') as fid:
                for f in parent.trainfiles:
                    fid.write(f)
                    fid.write('\n')
        except (ValueError, OSError, RuntimeError, TypeError, NameError,FileNotFoundError):
            print('ERROR: incorrect filename for saving')

def activate(parent, inactive):
    if inactive:
        parent.probcell = parent.model.apply(parent.stat)
    istat = parent.probcell
    parent.clabels[-2] = [istat.min(), (istat.max()-istat.min())/2, istat.max()]
    istat = istat - istat.min()
    istat = istat / istat.max()
    istat = istat / 1.3
    istat = istat + 0.1
    icols = 1 - istat
    parent.ops_plot[3][:,-1] = icols
    fig.class_masks(parent)

def disable(parent):
    parent.classbtn.setEnabled(False)
    parent.saveClass.setEnabled(False)
    parent.saveTrain.setEnabled(False)
    for btns in parent.classbtns.buttons():
        btns.setEnabled(False)

def add_to(parent):
    fname = parent.basename+'/iscell.npy'
    ftrue =  [f for f in parent.trainfiles if fname in f]
    if len(ftrue)==0:
        parent.trainfiles.append(parent.basename+'/iscell.npy')
    print('Repopulating classifier including current dataset:')
    parent.model = Classifier(classfile=None,
                                       trainfiles=parent.trainfiles,
                                       statclass=parent.statclass)
