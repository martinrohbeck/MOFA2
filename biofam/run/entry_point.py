import numpy as np
import pandas as pd
import scipy as s
import sys
from time import sleep
from time import time
import imp

from biofam.core.BayesNet import *
from biofam.build_model.build_model import *
from biofam.build_model.save_model import *
from biofam.build_model.train_model import train_model

class entry_point(object):
    def __init__(self):
        self.print_banner()
        self.dimensionalities = {}
        self.model = None

    def print_banner(self):
        """ Method to print the biofam banner """

        banner = r""" 

         _     _        __                       |￣￣￣￣￣￣￣|
        | |__ (_) ___  / _| __ _ _ __ ___        |              | 
        | '_ \| |/ _ \| |_ / _` | '_ ` _ \       |    MOFA+     |  
        | |_) | | (_) |  _| (_| | | | | | |      |              | 
        |_.__/|_|\___/|_|  \__,_|_| |_| |_|      | ＿＿＿＿＿＿_|  
                                                 (\__/) ||  
                                                 (•ㅅ•) ||  
                                                 / 　 づ 
        """

        print(banner)
        sys.stdout.flush()

    def set_data_matrix(self, data, samples_names_dict=None, features_names_dict=None):
        """ Method to input the data in a wide matrix

        PARAMETERS
        ----------
        data: two options:
            - a dictionary where each key is the view names and the object is a numpy array or a pandas data frame
            - a list where each element is a numpy array or a pandas data frame
            in both cases, the dimensions of each matrix must be (samples,features)
        samples_names_dict (optional): dictionary mapping groups names (keys) to samples names (values)
        features_names_dict (optional): dictionary mapping views names (keys) to features names (values)
        """

        # Sanity check
        if not isinstance(data, list):
            if isinstance(data, dict):
                data = list(data.values())
            else:
                print("Error: Data not recognised"); sys.stdout.flush(); exit()
        if len(data)==0:
            print("Error: Data is empty"); sys.stdout.flush(); exit()

        # Convert input data to numpy array format
        for m in range(len(data)):
            if isinstance(data[m], dict):
                data[m] = list(data[m].values())
            for p in range(len(data[m])):
                if not isinstance(data[m][p], np.ndarray):
                    if isinstance(data[m][p], pd.DataFrame):
                        data[m][p] = data[m][p].values
                    else:
                        print("Error, input data is not a numpy.ndarray or a pandas dataframe"); sys.stdout.flush(); exit()

        # Save dimensionalities
        M = self.dimensionalities["M"] = len(data)
        G = self.dimensionalities["G"] = len(data[0])
        N = self.dimensionalities["N"] = [data[0][p].shape[0] for p in range(len(data[0]))]
        D = self.dimensionalities["D"] = [data[m][0].shape[1] for m in range(len(data))]

        # Define views names and features names
        if features_names_dict is None:
            print("Views and features names not provided, using default naming convention:")
            print("- Views: view1, view2, ..., viewM")
            print("- Features: feature1_view1, featureD_viewM\n")
            self.data_opts['views_names'] = [ "view" + str(m) for m in range(M) ]
            self.data_opts['features_names'] = [ ["feature%d_view%d" % (d,m) for d in range(D[m])] for m in range(M) ]
        else:
            self.data_opts['views_names']  = [k for k in features_names_dict.keys()]
            self.data_opts['features_names'] = [v for v in features_names_dict.values()]


        # Define groups and samples names
        if samples_names_dict is None:
            print("Samples and groups names not provided, using default naming convention:")
            print("- Groups: group1, group2, ..., groupG")
            print("- Samples: sample1_group1, sample2_group1, sample1_group2, ..., sampleN_groupG\n")
            self.data_opts['groups_names'] = [ "group" + str(g) for g in range(G) ]
            self.data_opts['samples_names'] = [ "sample%d_group%d" % (n,g) for g in range(G) for n in range(N[g]) ]
        else:
            self.data_opts['groups_names'] = [k for k in samples_names_dict.keys()]
            self.data_opts['samples_names']  = [v for l in samples_names_dict.values() for v in l]

        # Set samples groups (list with dimensionality N where each row is the corresponding group name)
        # self.data_opts['samples_groups'] = [list(samples_names_dict.keys())[i] for i in range(len(self.data_opts['groups_names'])) for n in range(len(list(samples_names_dict.values())[i]))]

        # WHY THIS DOES NOT WORK?? asd = [ [self.data_opts['groups_names'][g]]*N[g] for g in range(G) ]
        self.data_opts['samples_groups'] = []
        for g in range(G):
            self.data_opts['samples_groups'].append( [self.data_opts['groups_names'][g]]*N[g] )
        self.data_opts['samples_groups'] = np.concatenate(self.data_opts['samples_groups'])


        # If everything successful, print verbose message
        for m in range(M):
            for g in range(G):
                print("Loaded view='%s' group='%s' with N=%d samples and D=%d features..." % (self.data_opts['views_names'][m],self.data_opts['groups_names'][g], data[m][g].shape[0], data[m][g].shape[1]))
        print("\n")

        # Concatenate groups
        for m in range(len(data)):
            data[m] = np.concatenate(data[m])
        self.dimensionalities["N"] = np.sum(self.dimensionalities["N"])

        # Process the data (center, scaling, etc.)
        self.data = process_data(data, self.data_opts, self.data_opts['samples_groups'])

    def set_data_from_files(self, inFiles, views, groups, header_rows=False, header_cols=False, delimiter=' '):
        """ Load the data """

        # TODO: sanity checks
        # - Check that input file exists
        # - Check that output directory exists: warning if not
        # TODO: Verbosity, print messages

        self.io_opts = {}

        # I/O
        if type(inFiles) is not list:
            inFiles = [inFiles]
        self.io_opts['input_files'] = inFiles
        self.io_opts['delimiter'] = delimiter

        # View names and group names (sample groups)
        if type(views) is not list:
            views = [views]
        if type(groups) is not list:
            groups = [groups]

        self.io_opts['views_names'] = views
        self.io_opts['groups_names'] = groups

        # Headers
        if header_rows is True:
            self.io_opts['rownames'] = 0
        else:
            self.io_opts['rownames'] = None

        if header_cols is True:
            self.io_opts['colnames'] = 0
        else:
            self.io_opts['colnames'] = None

        # Load observations
        self.data_opts.update(self.io_opts)
        # TODO reindex
        self.data, self.samples_groups = loadData(self.data_opts)

        # data frame needs reindexing if no header row
        if not header_rows:
            self.data[0] = self.data[0].reset_index(drop=True)
        # save feature, sample names, sample groups
        self.data_opts['samples_names'] = self.data[0].index
        self.data_opts['features_names'] = [dt.columns.values for dt in self.data]
        # TODO check that we have the right dictionary
        # TODO check that what is used later in the code is ok for this
        self.data_opts['samples_groups'] = self.samples_groups
        # taking unique view and group names in the
        ix = np.unique(self.data_opts['views_names'], return_index=True)[1]
        self.data_opts['views_names'] = (np.array(self.data_opts['views_names'])[ix]).tolist()
        ix = np.unique(self.data_opts['groups_names'], return_index=True)[1]
        self.data_opts['groups_names'] = (np.array(self.data_opts['groups_names'])[ix]).tolist()

        # set dimensionalities of the model
        M = self.dimensionalities["M"] = len(set(self.io_opts['views_names']))
        N = self.dimensionalities["N"] = self.data[0].shape[0]
        D = self.dimensionalities["D"] = [self.data[m].shape[1] for m in range(M)]
        self.dimensionalities["G"] = len(set(self.io_opts['groups_names']))

        self.data = process_data(self.data, self.data_opts,  self.samples_groups)

    def set_data_df(self, data):
        """Method to input the data in a long data.frame format

        PARAMETERS
        ----------
        data: pd.DataFrame
            a pandas DataFrame with columns ("sample","sample_group","feature","feature_group","value")
            the order is irrelevant
        """

        # Sanity checks
        assert hasattr(self, 'data_opts'), "Data options not defined"
        assert isinstance(data, pd.DataFrame), "'data' has to be an instance of pd.DataFrame"
        assert 'sample' in data.columns, "'data' has to contain the column 'sample'"
        assert 'sample_group' in data.columns, "'data' has to contain the column 'sample_group'"
        assert 'feature' in data.columns, "'data' has to contain the column 'feature'"
        assert 'feature_group' in data.columns, "'data' has to contain the column 'feature_group'"
        assert 'value' in data.columns, "'data' has to contain the column 'value'"

        # Define feature group names and sample group names
        self.data_opts['views_names'] = data["feature_group"].unique().tolist()
        self.data_opts['groups_names'] = data["sample_group"].unique().tolist()
        self.data_opts['features_names'] = data.groupby(["feature_group"])["feature"].unique()[self.data_opts['views_names']].tolist()
        self.data_opts['samples_names'] = data["sample"].unique().tolist()

        # Convert data frame to list of matrices
        data['feature'] = data['feature'].astype(str) + data['feature_group'].astype(str) # make sure there are no duplicated feature names before pivoting
        data_matrix = data.pivot(index='sample', columns='feature', values='value')

        # Sort rows and columns of the matrix according to the sample and feature names
        features_names_tmp = data.groupby(["feature_group"])["feature"].unique()[self.data_opts['views_names']].tolist()
        data_matrix = data_matrix.loc[self.data_opts['samples_names']]
        data_matrix = data_matrix[[y for x in features_names_tmp for y in x]]

        # Split into a list of views, each view being a matrix
        tmp_features = data[["feature","feature_group"]].drop_duplicates().groupby("feature_group")["feature"].nunique()
        nfeatures = tmp_features.loc[self.data_opts['views_names']]
        data_matrix = np.split(data_matrix, np.cumsum(nfeatures)[:-1], axis=1)

        # Define sample groups
        self.data_opts['samples_groups'] = data[['sample', 'sample_group']].drop_duplicates() \
                                            .set_index('sample').loc[self.data_opts['samples_names']] \
                                            .sample_group.tolist()

        # Define dimensionalities
        self.dimensionalities = {}
        self.dimensionalities["M"] = len(self.data_opts['views_names'])
        self.dimensionalities["N"] = len(self.data_opts['samples_names'])
        self.dimensionalities["G"] = len(self.data_opts['groups_names'])
        self.dimensionalities["D"] = [len(x) for x in self.data_opts['features_names']]

        # Count the number of features per view and the number of samples per group
        tmp_samples = data[["sample","sample_group","feature_group"]].drop_duplicates().groupby(["sample_group","feature_group"])["sample"].nunique()
        tmp_features = data[["feature","sample_group","feature_group"]].drop_duplicates().groupby(["sample_group","feature_group"])["feature"].nunique()

        # If everything successful, print verbose message
        for g in self.data_opts['groups_names']:
            for m in self.data_opts['views_names']:
                try:
                    print("Loaded group='%s' view='%s' with N=%d samples and D=%d features..." % (g, m, tmp_samples[g][m], tmp_features[g][m]) )
                except:
                    print("No data found for group='%s', view='%s',..." % (g, m))
        print("\n")

        # Process the data (i.e center, scale, etc.)
        self.data = process_data(data_matrix, self.data_opts, self.data_opts['samples_groups'])

    def set_data_from_anndata(self, adata, groups_label=None, use_raw=False):
        """ Method to input the data in AnnData format

        PARAMETERS
        ----------
        adata: an AnnotationData object
        groups_label (optional): a column name in adata.obs for grouping the samples
        use_raw (optional): use raw slot of AnnData as input values
        """

        # Sanity checks
        assert hasattr(self, 'data_opts'), "Data options not defined"

        # Check groups_label is defined properly
        n_groups = 1  # no grouping by default
        if groups_label is not None:
            if not isinstance(groups_label, str):
                print("Error: groups_label should be a string present in the observations column names"); sys.stdout.flush(); exit()
            if groups_label not in adata.obs.columns:
                print("Error: {} is not in observations names".format(groups_label)); sys.stdout.flush(); exit()
            n_groups = adata.obs[groups_label].unique().shape[0]

        # Save dimensionalities
        M = self.dimensionalities["M"] = 1
        G = self.dimensionalities["G"] = n_groups
        N = self.dimensionalities["N"] = adata.shape[0]
        D = self.dimensionalities["D"] = [adata.shape[1]]
        n_grouped = [adata.shape[0]] if n_groups == 1 else adata.obs.groupby(groups_label).size().values

        # Define views names and features names
        self.data_opts['views_names'] = ["rna"]
        self.data_opts['features_names'] = [adata.var_names]

        # Define groups and samples names
        if groups_label is None:
            self.data_opts['groups_names'] = "group1"
            self.data_opts['samples_names'] = adata.obs.index.values.tolist()
            self.data_opts['samples_groups'] = ["group1"] * N
        else:
            self.data_opts['groups_names'] = adata.obs[groups_label].unique()
            self.data_opts['samples_names'] = adata.obs.index.values.tolist()
            self.data_opts['samples_groups'] = adata.obs[groups_label].values

        # If everything successful, print verbose message
        for m in range(M):
            for g in range(G):
                print("Loaded view='%s' group='%s' with N=%d samples and D=%d features..." % (self.data_opts['views_names'][m], self.data_opts['groups_names'][g], n_grouped[g], D[m]))
        print("\n")
        # Process the data (center, scaling, etc.)
        if use_raw:
            self.data = process_data([np.array(adata.raw[:,adata.var_names].X.todense())], self.data_opts, self.data_opts['samples_groups'])
        else:
            self.data = process_data([adata.X], self.data_opts, self.data_opts['samples_groups'])

    def set_data_from_loom(self, loom, groups_label=None, layer=None):
        """ Method to input the data in Loom format

        PARAMETERS
        ----------
        loom: connection to loom file (loompy.loompy.LoomConnection)
        groups_label (optional): a key in loom.ca for grouping the samples
        layer (optional): a layer to be used instead of the main matrix
        """

        # Sanity checks
        assert hasattr(self, 'data_opts'), "Data options not defined"

        # Check groups_label is defined properly
        n_groups = 1  # no grouping by default
        if groups_label is not None:
            if not isinstance(groups_label, str):
                print("Error: groups_label should be a string present in the observations column names"); sys.stdout.flush(); exit()
            if groups_label not in loom.ca.keys():
                print("Error: {} is not in observations names".format(groups_label)); sys.stdout.flush(); exit()
            n_groups = pd.unique(loom.ca[groups_label]).shape[0]

        # Save dimensionalities
        M = self.dimensionalities["M"] = 1
        G = self.dimensionalities["G"] = n_groups
        N = self.dimensionalities["N"] = loom.shape[1]
        D = self.dimensionalities["D"] = [loom.shape[0]]
        n_grouped = [loom.shape[1]] if n_groups == 1 else pd.DataFrame({'label': loom.ca[groups_label]}).groupby('label').size().values

        # Define views names and features names
        self.data_opts['views_names'] = ["rna"]
        self.data_opts['features_names'] = [loom.ra.Accession] if 'Accession' in loom.ra.keys() else [loom.ra.Gene]

        # Define groups and samples names
        if groups_label is None:
            self.data_opts['groups_names'] = "group1"
            self.data_opts['samples_names'] = loom.ca.CellID
            self.data_opts['samples_groups'] = ["group1"] * N
        else:
            self.data_opts['groups_names'] = pd.unique(loom.ca[groups_label])
            self.data_opts['samples_names'] = loom.ca.CellID
            self.data_opts['samples_groups'] = loom.ca[groups_label]

        # If everything successful, print verbose message
        for m in range(M):
            for g in range(G):
                print("Loaded view='%s' group='%s' with N=%d samples and D=%d features..." % (self.data_opts['views_names'][m], self.data_opts['groups_names'][g], n_grouped[g], D[m]))
        print("\n")

        # Process the data (center, scaling, etc.)
        if layer is not None:
            self.data = process_data([loom.layers[layer]], self.data_opts, self.data_opts['samples_groups'])
        else:
            self.data = process_data([loom[:,:]], self.data_opts, self.data_opts['samples_groups'])

    def set_train_options(self,
        iter=5000, startELBO=1, elbofreq=1, startSparsity=100, tolerance=0.01, convergence_mode="medium",
        startDrop=1, freqDrop=1, dropR2=None, nostop=False, verbose=False, quiet=False, seed=None,
        schedule=None, gpu_mode=False, Y_ELBO_TauTrick=True,
        ):
        """ Set training options """

        # Sanity checks
        assert hasattr(self, 'model_opts'), "Model options have to be defined before training options"

        self.train_opts = {}

        # Maximum number of iterations
        self.train_opts['maxiter'] = int(iter)

        # Lower bound computation frequency
        if elbofreq is None or elbofreq==0: elbofreq=iter+1
        self.train_opts['elbofreq'] = int(elbofreq)
        if startELBO==0: startELBO=1
        if startELBO==None: startELBO=iter+1
        self.train_opts['start_elbo'] = int(startELBO)

        # Verbosity
        self.train_opts['verbose'] = bool(verbose)
        self.train_opts['quiet'] = bool(quiet)

        # GPU mode
        if gpu_mode:
            # first see if cupy is installed and give instructions if not
            # if installed import to check that everything goes well
            try:
                import cupy as cp
                print("GPU mode is activated\n")
            except ImportError:
                print("GPU mode is activated, but GPU not found... switching to CPU mode")
                print('For GPU mode, you need:')
                print('1 - Make sure that you are running MOFA+ on a machine with an NVIDIA GPU')
                print('2 - Install CUPY following instructions on https://docs-cupy.chainer.org/en/stable/install.html\n')
                sys.stdout.flush()
                gpu_mode = False
        self.train_opts['gpu_mode'] = gpu_mode

        # Minimum Variance explained threshold to drop inactive factors
        if dropR2 is not None: 
            dropR2 = float(dropR2)
            if dropR2 < 0: dropR2 = None
        self.train_opts['drop'] = { "min_r2":dropR2 }
        self.train_opts['start_drop'] = int(startDrop)
        self.train_opts['freq_drop'] = int(freqDrop)
        if ((dropR2 is not None) & (verbose is True)): print("\nDropping factors with minimum threshold of {0}% variance explained\n".format(dropR2))

        if ((dropR2 is not None) & (self.dimensionalities["N"]>1e4)):
            print("Warning: actively dropping factors during model training can be slow in large data sets.")
            print("Consider training the model with set drop_factor_threshold = -1 and prune them a posteriori")
        

        # Tolerance level for convergence
        self.train_opts['tolerance'] = float(tolerance)
        self.train_opts['convergence_mode'] = str(convergence_mode)
        if verbose: print("Convergence mode: %s\n" % convergence_mode)

        # Do no stop even when convergence criteria is met
        self.train_opts['forceiter'] = nostop

        # Iteration to activate spike and slab sparsity
        self.train_opts['start_sparsity'] = int(startSparsity)

        # By default, stochastic training is not activated
        self.train_opts['stochastic'] = False

        # Training schedule
        if schedule is None:
            schedule = ['Y', 'Z', 'W', 'Tau']
            # schedule = ['Y', 'W', 'Z', 'Tau']

            # Insert ThetaW after W if Spike and Slab prior on W
            if self.model_opts['sl_w']:
                ix = schedule.index("W"); schedule.insert(ix+1, 'ThetaW')

            # Insert ThetaZ after Z if Spike and Slab prior on Z
            if self.model_opts['sl_z']:
                ix = schedule.index("Z"); schedule.insert(ix+1, 'ThetaZ')

            # Insert AlphaW after W if ARD prior on W
            if self.model_opts['ard_w']:
                ix = schedule.index("W"); schedule.insert(ix+1, 'AlphaW')

            # Insert AlphaZ after Z if ARD prior on Z
            if self.model_opts['ard_z']:
                ix = schedule.index("Z"); schedule.insert(ix+1, 'AlphaZ')

        else:
            assert set(["Y","W","Z","Tau"]) <= set(schedule)
            if self.model_opts['ard_z']: assert "AlphaZ" in schedule
            if self.model_opts['ard_w']: assert "AlphaW" in schedule
            if self.model_opts['sl_z']: assert "ThetaZ" in schedule
            if self.model_opts['sl_w']: assert "ThetaW" in schedule

        self.train_opts['schedule'] = schedule

        # Seed
        if seed is None:  # Seed for the random number generator
            seed = int(round(time()*1000)%1e6)
        self.train_opts['seed'] = int(seed)
        s.random.seed(self.train_opts['seed'])

        # Use TauTrick to speed up ELBO computation?
        self.train_opts['Y_ELBO_TauTrick'] = Y_ELBO_TauTrick

    def set_stochastic_options(self, learning_rate=1., forgetting_rate=0., batch_size=1., start_stochastic=1):

        # Sanity checks
        assert hasattr(self, 'train_opts'), "Train options not defined"
        assert 0 < learning_rate <= 1, 'Learning rate must range from 0 and 1'
        assert 0 < forgetting_rate <= 1, 'Forgetting rate must range from 0 and 1'
        assert 0 < batch_size <= 1, 'Batch size must range from 0 to 1'
        assert start_stochastic >= 1, 'start_stochastic must be >= 1'

        self.train_opts['stochastic'] = True
        self.train_opts['Y_ELBO_TauTrick'] = False # TauTrick only works in non-stochastic mode
        self.train_opts['learning_rate'] = learning_rate
        self.train_opts['forgetting_rate'] = forgetting_rate
        self.train_opts['start_stochastic'] = start_stochastic
        self.train_opts['batch_size'] = batch_size


        self.train_opts['drop']["min_r2"] = None

    def set_model_options(self, factors, likelihoods, sl_z=False, sl_w=False, ard_z=False, ard_w=False):
        """ Set model options """

        # TODO: SANITY CHECKS AND:
        # - learnTheta should be replaced by learn_sparsity

        self.model_opts = {}

        # Define whether to use sample-wise spike and slab prior for Z
        self.model_opts['sl_z'] = sl_z

        # Define whether to use feature-wise spike and slab prior for W
        self.model_opts['sl_w'] = sl_w

        # Define whether to use sample_group and factor-wise ARD prior for Z
        self.model_opts['ard_z'] = ard_z

        # Define whether to use view and factor-wise ARD prior for W
        self.model_opts['ard_w'] = ard_w

        # Define initial number of latent factors
        self.dimensionalities["K"] = self.model_opts['factors'] = int(factors)

        # Define likelihoods
        self.model_opts['likelihoods'] = likelihoods
        if isinstance(self.model_opts['likelihoods'], str):
            self.model_opts['likelihoods'] = [self.model_opts['likelihoods']]
        assert len(self.model_opts['likelihoods'])==self.dimensionalities["M"], "Please specify one likelihood for each view"
        assert set(self.model_opts['likelihoods']).issubset(set(["gaussian","bernoulli","poisson",'zero_inflated'])), "Available likelihoods are 'gaussian','bernoulli', 'poisson', 'zero_inflated'"

    def set_data_options(self, likelihoods, center_features_per_group=True, scale_views=False, scale_groups=False, mask=None, mask_zeros=False):
        """ Set data processing options """

        # TODO: more verbose messages
        # TODO Sanity checks
        self.data_opts = {}

        # Define likelihoods
        if type(likelihoods) is not list:
          likelihoods = [likelihoods]
        assert set(likelihoods).issubset(set(["gaussian", "bernoulli", "poisson", "zero_inflated"]))
        self.data_opts["likelihoods"] = likelihoods
        M = len(likelihoods)

        # Center features
        self.data_opts['center_features_per_group'] = center_features_per_group

        # Scale views to unit variance
        self.data_opts['scale_views'] = scale_views
        if (scale_views): print("Scaling views to unit variance...\n")

        # Scale groups to unit variance
        self.data_opts['scale_groups'] = scale_groups
        if (scale_groups): print("Scaling groups to unit variance...\n")

        # Do we want to mask zeros in the data (provide list if depends on view)
        self.data_opts['mask_zeros'] = mask_zeros

        # Mask values
        if mask is not None:
            assert len(mask)==M, "Length of 'mask' argument must be equal to the number of views"
            self.data_opts['mask'] = mask
        else:
            self.data_opts['mask'] = [0]*M

    def build(self):
        """ Build the model """

        # Sanity checks
        assert hasattr(self, 'train_opts'), "Training options not defined"
        assert hasattr(self, 'model_opts'), "Model options not defined"
        assert hasattr(self, 'dimensionalities'), "Dimensionalities are not defined"

        # Build the nodes
        tmp = buildBiofam(self.data, self.data_opts, self.model_opts, self.dimensionalities)

        # Create BayesNet class
        if self.train_opts['stochastic']:
            self.model = StochasticBayesNet(self.dimensionalities, tmp.get_nodes())
        else:
            self.model = BayesNet(self.dimensionalities, tmp.get_nodes())

    def run(self):
        """ Run the model """

        # Sanity checks
        assert hasattr(self, 'model_opts'), "Model options not defined"
        assert hasattr(self, 'train_opts'), "Train options not defined"
        assert hasattr(self, 'data_opts'), "Data options not defined"

        # Fetch training schedule (order of updates for the different nodes)
        if 'schedule' in self.train_opts:
            assert set(self.train_opts['schedule']) == set(list(self.model.getNodes().keys())), "Some nodes defined in the training schedule are not present in the model, or viceversa"
        else:
            self.train_opts['schedule'] = self.model_builder.schedule

        # Set training options
        self.model.setTrainOptions(self.train_opts)

        # Train the model
        train_model(self.model)

    def save(self, outfile):
        """ Save the model in an hdf5 file """

        # Sanity checks
        assert hasattr(self, 'data'), "Data has to be defined before training the model"
        assert hasattr(self, 'model'), "No trained model found"

        # Create output directory
        if not os.path.isdir(os.path.dirname(outfile)) and (os.path.dirname(outfile) != ''):
            print("Output directory does not exist, creating it...")
            os.makedirs(os.path.dirname(outfile))
        print("Saving model in %s...\n" % outfile)

        # Save the model
        tmp = saveModel(
          model = self.model,
          outfile = outfile,
          data = self.data,
          samples_groups = self.data_opts['samples_groups'],
          train_opts = self.train_opts,
          model_opts = self.model_opts,
          samples_names = self.data_opts['samples_names'],
          features_names = self.data_opts['features_names'],
          views_names = self.data_opts['views_names'],
          compression_level = 9
        )

        # If all likelihoods are gaussian there is no need to save the expectations of Y, just saving the data is enough
        if all([i=="gaussian" for i in self.model_opts["likelihoods"]]):
            tmp.saveExpectations(nodes=["W","Z"])
        else:
            tmp.saveExpectations(nodes=["Y","W","Z"])

        tmp.saveModelOptions()
        tmp.saveTrainOptions()
        tmp.saveTrainingStats()
        tmp.saveData()


def mofa(adata, groups_label=None, use_raw=False,
         likelihood: str = "gaussian", n_factors: int = 10,
         n_iterations: int = 1000, convergence_mode: str = "fast",
         seed: int = 1, outfile: str = "/tmp/mofa_model.hdf5",
         verbose = False, quiet = True, copy = False):
    """
    Helper function to init and build the model in a single call
    from annotation data object

    PARAMETERS
    ----------
    adata: an AnnotationData object
    groups_label (optional): a column name in adata.obs for grouping the samples
    use_raw (optional): use raw slot of AnnData as input values
    likelihood: likelihood to use, default is gaussian
    n_factors: number of factors to train the model with
    n_iterations: upper limit on the number of iterations
    convergence_mode: fast, medium, or slow convergence mode
    seed: random seed
    outfile: path to HDF5 file to store the model
    verbose: print verbose information during traing
    quiet: silence messages during training procedure
    copy: return a copy of AnnData instead of writing to the provided object
    """

    ent = entry_point()
    
    lik = [likelihood]
    
    ent.set_data_options(lik, center_features_per_group=True, scale_features=True, scale_views=False)
    ent.set_data_from_anndata(adata, groups_label=groups_label, use_raw=use_raw)
    ent.set_model_options(ard_z=True, sl_w=True, sl_z=True, ard_w=True, factors=n_factors, likelihoods=lik)
    ent.set_train_options(iter=n_iterations, convergence_mode=convergence_mode, seed=seed, verbose=False, quiet=True)

    ent.build()
    ent.run()
    ent.save(outfile)

    try:
        import h5py
    except ImportError:
        h5py = None


    if h5py:
        f = h5py.File(outfile)
        if copy:
            adata = adata.copy()
        adata.obsm['X_mofa'] = np.concatenate([v[:,:] for k, v in f['expectations']['Z'].items()], axis=1).T
        adata.varm['LFs'] = np.concatenate([v[:,:] for k, v in f['expectations']['W'].items()], axis=1).T
        if copy:
            return adata
        else:
            print("Saved MOFA embeddings in adata.obsm.X_mofa slot and their loadings in adata.varm.LFs.")
    else:
        print("Can not add embeddings and loadings to AnnData object since h5py is not installed.")


