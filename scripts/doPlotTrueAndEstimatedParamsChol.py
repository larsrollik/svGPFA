
import sys
import os
import pdb
import pickle
import configparser
import numpy as np
import torch
import plotly.graph_objects as go
import plotly
from plotly.subplots import make_subplots
import plotly.tools as tls
sys.path.append("../src")
import utils.svGPFA.configUtils
import utils.svGPFA.miscUtils
import plot.svGPFA.plotUtilsPlotly

def main(argv):
    if len(argv)!=2:
        print("Usage {:s} <estimation number> ".format(argv[0]))
        return

    estNumber = int(argv[1])
    gpRegularization = 1e-3
    estMetaDataFilename = "results/{:08d}_estimation_metaData.ini".format(estNumber)
    modelSaveFilename = "results/{:08d}_estimatedModel.pickle".format(estNumber)
    kernelsParamsFigFilenamePattern = "figures/{:08d}_trueAndEstimatedKernelsParams.{{:s}}".format(estNumber)
    latentsMeansFigFilenamePattern = "figures/{:08d}_trueAndEstimatedLatentsMeans.{{:s}}".format(estNumber)
    embeddingParamsFigFilenamePattern = "figures/{:08d}_trueAndEstimatedEmbeddingParams.{{:s}}".format(estNumber)

    estMetaDataConfig = configparser.ConfigParser()
    estMetaDataConfig.read(estMetaDataFilename)
    simResNumber = int(estMetaDataConfig["simulation_params"]["simResNumber"])
    simMetaDataFilename = "results/{:08d}_simulation_metaData.ini".format(simResNumber)
    simMetaDataConfig = configparser.ConfigParser()
    simMetaDataConfig.read(simMetaDataFilename)
    simInitConfigFilename = simMetaDataConfig["simulation_params"]["simInitConfigFilename"]
    simInitConfig = configparser.ConfigParser()
    simInitConfig.read(simInitConfigFilename)
    nIndPointsPerLatent = [int(str) for str in simInitConfig["control_variables"]["nIndPointsPerLatent"][1:-1].split(",")]
    nLatents = len(nIndPointsPerLatent)
    nNeurons = int(simInitConfig["control_variables"]["nNeurons"])
    trialsLengths = [float(str) for str in simInitConfig["control_variables"]["trialsLengths"][1:-1].split(",")]
    nTrials = len(trialsLengths)
    dtSimulate = float(simInitConfig["control_variables"]["dtCIF"])

    kernels = utils.svGPFA.configUtils.getKernels(nLatents=nLatents, config=simInitConfig, forceUnitScale=True)
    # latentsMeansFuncs[r][k] \in lambda(t)
#     tLatentsMeansFuncs = utils.svGPFA.configUtils.getLatentsMeansFuncs(nLatents=nLatents, nTrials=nTrials, config=simInitConfig)
    CFilename = simInitConfig["embedding_params"]["C_filename"]
    dFilename = simInitConfig["embedding_params"]["d_filename"]
    trueC, trueD = utils.svGPFA.configUtils.getLinearEmbeddingParams(nNeurons=nNeurons, nLatents=nLatents, CFilename=CFilename, dFilename=dFilename)
    trialsTimes = utils.svGPFA.miscUtils.getTrialsTimes(trialsLengths=trialsLengths, dt=dtSimulate)

    # latentsMeansSamples[r][k,t]
#     tLatentsMeans = utils.svGPFA.miscUtils.getLatentsMeanFuncsSamples(latentsMeansFuncs=
#                                                 tLatentsMeansFuncs,
#                                                trialsTimes=trialsTimes,
#                                                dtype=trueC.dtype)

    with open(modelSaveFilename, "rb") as f: savedResults = pickle.load(f)
    model = savedResults["model"]
    kernelsParams = model.getKernelsParams()
    with torch.no_grad():
        latentsMeans, _ = model.predictLatents(newTimes=trialsTimes[0])
    estimatedC, estimatedD = model.getSVEmbeddingParams()
    fig = plot.svGPFA.plotUtilsPlotly.getPlotTrueAndEstimatedKernelsParams(
        trueKernels=kernels, 
        estimatedKernelsParams=kernelsParams)
    fig.write_image(kernelsParamsFigFilenamePattern.format("png"))
    fig.write_html(kernelsParamsFigFilenamePattern.format("html"))

    # qMu[r] \in nTrials x nInd[k] x 1
#     plot.svGPFA.plotUtilsPlotly.plotTrueAndEstimatedLatentsMeans(trueLatentsMeans=tLatentsMeans,
#                                      estimatedLatentsMeans=latentsMeans,
#                                      trialsTimes=trialsTimes)
#     fig.write_image(latentsMeansFigFilenamePattern.format("png"))
#     fig.write_html(latentsMeansFigFilenamePattern.format("html"))

    fig = plot.svGPFA.plotUtilsPlotly.getPlotTrueAndEstimatedEmbeddingParams(
        trueC=trueC, trueD=trueD,
        estimatedC=estimatedC, estimatedD=estimatedD)
    fig.write_image(embeddingParamsFigFilenamePattern.format("png"))
    fig.write_html(embeddingParamsFigFilenamePattern.format("html"))

    pdb.set_trace()

if __name__=="__main__":
    main(sys.argv)