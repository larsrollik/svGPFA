
import sys
import pdb
import os
import math
from scipy.io import loadmat
import numpy as np
import torch
sys.path.append("../src")
import utils.svGPFA.miscUtils
import stats.kernels
import stats.svGPFA.kernelsMatricesStore
import stats.svGPFA.svPosteriorOnIndPoints
import stats.svGPFA.svPosteriorOnLatents

def test_computeMeansAndVars_allTimes():
    tol = 5e-6
    dataFilename = os.path.join(os.path.dirname(__file__), "data/Estep_Objective_PointProcess_svGPFA.mat")

    mat = loadmat(dataFilename)
    nLatents = mat["Z"].shape[0]
    nTrials = mat["Z"][0,0].shape[2]
    qMu0 = [torch.from_numpy(mat["q_mu"][(0,i)]).type(torch.DoubleTensor).permute(2,0,1) for i in range(nLatents)]
    qSVec0 = [torch.from_numpy(mat["q_sqrt"][(0,i)]).type(torch.DoubleTensor).permute(2,0,1) for i in range(nLatents)]
    qSDiag0 = [torch.from_numpy(mat["q_diag"][(0,i)]).type(torch.DoubleTensor).permute(2,0,1) for i in range(nLatents)]
    srQSigma0Vecs = utils.svGPFA.miscUtils.getSRQSigmaVec(qSVec=qSVec0, qSDiag=qSDiag0)
    t = torch.from_numpy(mat["ttQuad"]).type(torch.DoubleTensor).permute(2, 0, 1)
    Z0 = [torch.from_numpy(mat["Z"][(i,0)]).type(torch.DoubleTensor).permute(2,0,1) for i in range(nLatents)]
    mu_k = torch.from_numpy(mat["mu_k_Quad"]).type(torch.DoubleTensor).permute(2,0,1)
    var_k = torch.from_numpy(mat["var_k_Quad"]).type(torch.DoubleTensor).permute(2,0,1)
    kernelNames = mat["kernelNames"]
    hprs = mat["hprs"]

    kernels = [[None] for k in range(nLatents)]
    kernelsParams0 = [[None] for k in range(nLatents)]
    for k in range(nLatents):
        if np.char.equal(kernelNames[0,k][0], "PeriodicKernel"):
            kernels[k] = stats.kernels.PeriodicKernel(scale=1.0)
            kernelsParams0[k] = torch.tensor([float(hprs[k,0][0]),
                                              float(hprs[k,0][1])],
                                             dtype=torch.double)
        elif np.char.equal(kernelNames[0,k][0], "rbfKernel"):
            kernels[k] = stats.kernels.ExponentialQuadraticKernel(scale=1.0)
            kernelsParams0[k] = torch.tensor([float(hprs[k,0][0])],
                                             dtype=torch.double)
        else:
            raise ValueError("Invalid kernel name: %s"%(kernelNames[k]))

    qU = stats.svGPFA.svPosteriorOnIndPoints.SVPosteriorOnIndPointsChol()
    indPointsLocsKMS = stats.svGPFA.kernelsMatricesStore.IndPointsLocsKMS_Chol()
    indPointsLocsAndTimesKMS = stats.svGPFA.kernelsMatricesStore.IndPointsLocsAndAllTimesKMS()
    qK = stats.svGPFA.svPosteriorOnLatents.SVPosteriorOnLatentsAllTimes(svPosteriorOnIndPoints=qU,
                                      indPointsLocsKMS=indPointsLocsKMS,
                                      indPointsLocsAndTimesKMS=
                                       indPointsLocsAndTimesKMS)

    qUParams0 = {"qMu0": qMu0, "srQSigma0Vecs": srQSigma0Vecs}
    kmsParams0 = {"kernelsParams0": kernelsParams0,
                  "inducingPointsLocs0": Z0}

    qU.setInitialParams(initialParams=qUParams0)

    indPointsLocsKMS.setKernels(kernels=kernels)
    indPointsLocsKMS.setInitialParams(initialParams=kmsParams0)
    indPointsLocsKMS.setEpsilon(epsilon=1e-5) # Fix: need to read indPointsLocsKMSEpsilon from Matlab's CI test data
    indPointsLocsKMS.buildKernelsMatrices()

    indPointsLocsAndTimesKMS.setKernels(kernels=kernels)
    indPointsLocsAndTimesKMS.setInitialParams(initialParams=kmsParams0)
    indPointsLocsAndTimesKMS.setTimes(times=t)
    indPointsLocsAndTimesKMS.buildKernelsMatrices()

    qKMu, qKVar = qK.computeMeansAndVars()

    qKMuError = math.sqrt(((mu_k-qKMu)**2).mean())
    assert(qKMuError<tol)
    qKVarError = math.sqrt(((var_k-qKVar)**2).mean())
    assert(qKVarError<tol)

def test_computeMeansAndVars_assocTimes():
    tol = 5e-6
    dataFilename = os.path.join(os.path.dirname(__file__), "data/Estep_Objective_PointProcess_svGPFA.mat")

    mat = loadmat(dataFilename)
    nLatents = mat["Z"].shape[0]
    nTrials = mat["Z"][0,0].shape[2]
    qMu0 = [torch.from_numpy(mat["q_mu"][(0,i)]).type(torch.DoubleTensor).permute(2,0,1) for i in range(nLatents)]
    qSVec0 = [torch.from_numpy(mat["q_sqrt"][(0,i)]).type(torch.DoubleTensor).permute(2,0,1) for i in range(nLatents)]
    qSDiag0 = [torch.from_numpy(mat["q_diag"][(0,i)]).type(torch.DoubleTensor).permute(2,0,1) for i in range(nLatents)]
    srQSigma0Vecs = utils.svGPFA.miscUtils.getSRQSigmaVec(qSVec=qSVec0, qSDiag=qSDiag0)
    Z0 = [torch.from_numpy(mat["Z"][(i,0)]).type(torch.DoubleTensor).permute(2,0,1) for i in range(nLatents)]
    Y = [torch.from_numpy(mat["Y"][tr,0]).type(torch.DoubleTensor) for tr in range(nTrials)]
    mu_k = [torch.from_numpy(mat["mu_k_Spikes"][0,tr]).type(torch.DoubleTensor) for tr in range(nTrials)]
    var_k = [torch.from_numpy(mat["var_k_Spikes"][0,tr]).type(torch.DoubleTensor) for tr in range(nTrials)]
    kernelNames = mat["kernelNames"]
    hprs = mat["hprs"]

    kernels = [[None] for k in range(nLatents)]
    kernelsParams0 = [[None] for k in range(nLatents)]
    for k in range(nLatents):
        if np.char.equal(kernelNames[0,k][0], "PeriodicKernel"):
            kernels[k] = stats.kernels.PeriodicKernel(scale=1.0)
            kernelsParams0[k] = torch.tensor([float(hprs[k,0][0]),
                                              float(hprs[k,0][1])],
                                             dtype=torch.double)
        elif np.char.equal(kernelNames[0,k][0], "rbfKernel"):
            kernels[k] = stats.kernels.ExponentialQuadraticKernel(scale=1.0)
            kernelsParams0[k] = torch.tensor([float(hprs[k,0][0])],
                                             dtype=torch.double)
        else:
            raise ValueError("Invalid kernel name: %s"%(kernelNames[k]))

    qU = stats.svGPFA.svPosteriorOnIndPoints.SVPosteriorOnIndPointsChol()
    indPointsLocsKMS = stats.svGPFA.kernelsMatricesStore.IndPointsLocsKMS_Chol()
    indPointsLocsAndTimesKMS = stats.svGPFA.kernelsMatricesStore.IndPointsLocsAndAssocTimesKMS()
    qK = stats.svGPFA.svPosteriorOnLatents.SVPosteriorOnLatentsAssocTimes(svPosteriorOnIndPoints=qU,
                                        indPointsLocsKMS=indPointsLocsKMS,
                                        indPointsLocsAndTimesKMS=
                                         indPointsLocsAndTimesKMS)

    # qSigma0[k] \in nTrials x nInd[k] x nInd[k]
    qUParams0 = {"qMu0": qMu0, "srQSigma0Vecs": srQSigma0Vecs}
    kmsParams0 = {"kernelsParams0": kernelsParams0,
                  "inducingPointsLocs0": Z0}
    qU.setInitialParams(initialParams=qUParams0)

    indPointsLocsKMS.setKernels(kernels=kernels)
    indPointsLocsKMS.setInitialParams(initialParams=kmsParams0)
    indPointsLocsKMS.setEpsilon(epsilon=1e-5) # Fix: need to read indPointsLocsKMSEpsilon from Matlab's CI test data
    indPointsLocsKMS.buildKernelsMatrices()

    indPointsLocsAndTimesKMS.setKernels(kernels=kernels)
    indPointsLocsAndTimesKMS.setInitialParams(initialParams=kmsParams0)
    indPointsLocsAndTimesKMS.setTimes(times=Y)
    indPointsLocsAndTimesKMS.buildKernelsMatrices()

    qKMu, qKVar = qK.computeMeansAndVars()

    for tr in range(nTrials):
        qKMuError = math.sqrt(((mu_k[tr]-qKMu[tr])**2).mean())
        assert(qKMuError<tol)
        qKVarError = math.sqrt(((var_k[tr]-qKVar[tr])**2).mean())
        assert(qKVarError<tol)

if __name__=="__main__":
    test_computeMeansAndVars_allTimes()
    test_computeMeansAndVars_assocTimes()
