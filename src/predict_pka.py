#!/usr/bin/env python
# coding: utf-8

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import RDLogger
RDLogger.DisableLog('rdApp.*')
from rdkit.Chem.MolStandardize import rdMolStandardize

import os.path as osp
import numpy as np
import pandas as pd
#import os # 18/03/24 GALC change

import torch
import warnings
warnings.filterwarnings("ignore") #Supressing warning from torch_geometric GALC change 31/03/24

from MolGpKa.src.utils.ionization_group import get_ionization_aid
from MolGpKa.src.utils.descriptor import mol2vec
from MolGpKa.src.utils.net import GCNNet

#os.chdir(osp.dirname(osp.abspath(__file__))) # 18/03/24 GALC change
root = osp.abspath(osp.dirname(__file__))

def load_model(model_file, device="cpu"):
    model= GCNNet().to(device)
    model.load_state_dict(torch.load(model_file, map_location=device))
    model.eval()
    return model

def model_pred(m2, aid, model, device="cpu"):
    data = mol2vec(m2, aid)
    with torch.no_grad():
        data = data.to(device)
        pKa = model(data)
        pKa = pKa.cpu().numpy()
        pka = pKa[0][0]
    return pka

def predict_acid(mol):
    model_file = osp.join(root, "../models/weight_acid.pth")
    #model_file = "/users/glara/Carbohidrate_ligand/Sucrose-PBAs/Solvent/HostDesigner/ab-initio_screening/molecules_screening/geometries_screen/GB_GA/MolGpKa/models/weight_acid.pth"
    model_acid = load_model(model_file)

    acid_idxs= get_ionization_aid(mol, acid_or_base="acid")
    acid_res = {}
    for aid in acid_idxs:
        apka = model_pred(mol, aid, model_acid)
        acid_res.update({aid:apka})
    return acid_res

def predict_base(mol):
    model_file = osp.join(root, "../models/weight_base.pth")
    #model_file = "/users/glara/Carbohidrate_ligand/Sucrose-PBAs/Solvent/HostDesigner/ab-initio_screening/molecules_screening/geometries_screen/GB_GA/MolGpKa/models/weight_base.pth"
    #print('root:',root)
    model_base = load_model(model_file)

    base_idxs= get_ionization_aid(mol, acid_or_base="base")
    base_res = {}
    for aid in base_idxs:
        bpka = model_pred(mol, aid, model_base) 
        base_res.update({aid:bpka})
    return base_res

def predict(mol, uncharged=True):
    if uncharged:
        un = rdMolStandardize.Uncharger()
        mol = un.uncharge(mol)
        mol = Chem.MolFromSmiles(Chem.MolToSmiles(mol))
    mol = AllChem.AddHs(mol)
    base_dict = predict_base(mol)
    acid_dict = predict_acid(mol)
    return base_dict, acid_dict

def predict_for_protonate(mol, uncharged=True):
    if uncharged:
        un = rdMolStandardize.Uncharger()
        mol = un.uncharge(mol)
        mol = Chem.MolFromSmiles(Chem.MolToSmiles(mol))
    mol = AllChem.AddHs(mol)
    base_dict = predict_base(mol)
    acid_dict = predict_acid(mol)
    return base_dict, acid_dict, mol


if __name__=="__main__":
    mol = Chem.MolFromSmiles("CN(C)CCCN1C2=CC=CC=C2SC2=C1C=C(C=C2)C(C)=O")
    base_dict, acid_dict = predict(mol)
    print("base:",base_dict)
    print("acid:",acid_dict)

