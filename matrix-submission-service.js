/**
 * Matrix Submission Service - Handles matrix-based form value submissions to backend services
 */
class MatrixSubmissionService {
  constructor() {
    this.submitParameterUrl = 'http://localhost:3040/append/';
    this.submitCompleteSetUrl = 'http://localhost:3052/append/';
    this.formatterUrl = 'http://localhost:3050/formatter/';
    this.module1Url = 'http://localhost:3051/module1/';
    this.configModulesUrl = 'http://localhost:3053/config_modules/';
    this.tableUrl = 'http://localhost:3054/table/';
  }

  /**
   * Submit the matrix-based form values to the server
   * @param {Object} matrixFormValues The matrix form values object
   * @param {string} versionId The version ID
   * @returns {Promise<Object>} The response from the server
   */
  async submitMatrixFormValues(matrixFormValues, versionId) {
    try {
      // Prepare filtered values format with matrix data
      const filteredValues = this.prepareFilteredValues(matrixFormValues, versionId);
      
      // Submit the filtered values
      const submitResponse = await this.submitFilteredValues(filteredValues, versionId);
      
      // Run the formatter to process the submitted values
      const formatterResponse = await this.runFormatter(versionId);
      
      // Run module1 to build the configuration matrix
      const module1Response = await this.runModule1(versionId);
      
      // Run config_modules to create configuration modules
      const configModulesResponse = await this.runConfigModules(versionId);
      
      // Run table module to create the variable table
      const tableResponse = await this.runTable(versionId);
      
      return {
        submit: submitResponse,
        formatter: formatterResponse,
        module1: module1Response,
        configModules: configModulesResponse,
        table: tableResponse
      };
    } catch (error) {
      console.error('Error submitting matrix form values:', error);
      throw error;
    }
  }

  /**
   * Prepare filtered values from matrix form values
   * @param {Object} matrixFormValues The matrix form values
   * @param {string} versionId The version ID (e.g., 'v1', 'v2')
   * @returns {string} The filtered values JSON string
   */
  prepareFilteredValues(matrixFormValues, versionId) {
    const filteredValues = { filteredValues: [] };
    const activeVersion = versionId || matrixFormValues.versions.active;
    const activeZone = matrixFormValues.zones.active;
    
    // Extract the numeric version from the versionId (e.g., 'v1' -> '1')
    const numericVersion = activeVersion.replace(/\D/g, '');
    
    // Process each parameter in the matrix
    Object.keys(matrixFormValues.formMatrix).forEach(paramId => {
      const param = matrixFormValues.formMatrix[paramId];
      
      // Skip parameters that don't have matrix values for the active version/zone
      if (!param.matrix[activeVersion] || !param.matrix[activeVersion][activeZone]) {
        return;
      }
      
      // Get the parameter value for the active version and zone
      const value = param.matrix[activeVersion][activeZone];
      
      // Add the parameter to the filtered values array
      filteredValues.filteredValues.push({
        id: paramId,
        value: value,
        start: param.efficacyPeriod.start.value,
        end: param.efficacyPeriod.end.value,
        remarks: param.remarks || ""
      });
      
      // Special handling for vector values (Amount4, Amount5, Amount6, Amount7)
      // For vector quantities (vAmountX) and prices (rAmountY)
      if (param.dynamicAppendix && param.dynamicAppendix.itemState) {
        const itemState = param.dynamicAppendix.itemState;
        
        // Only include items that are turned on (status = 'on')
        if (itemState.status === 'on') {
          // Handle vKey vector items
          if (itemState.vKey && paramId.includes('vAmount')) {
            const vIndex = parseInt(paramId.replace('vAmount', ''));
            filteredValues.filteredValues.push({
              id: `variableCostsAmount4_${vIndex - 39}`,
              value: value,
              start: param.efficacyPeriod.start.value,
              end: param.efficacyPeriod.end.value,
              remarks: `Vector Quantity Item ${vIndex - 39}`
            });
          }
          
          // Handle rKey vector items
          if (itemState.rKey && paramId.includes('rAmount')) {
            const rIndex = parseInt(paramId.replace('rAmount', ''));
            filteredValues.filteredValues.push({
              id: `amounts_per_unitAmount5_${rIndex - 59}`,
              value: value,
              start: param.efficacyPeriod.start.value,
              end: param.efficacyPeriod.end.value,
              remarks: `Vector Price Item ${rIndex - 59}`
            });
          }
        }
      }
    });
    
    return JSON.stringify(filteredValues, null, 2);
  }

  /**
   * Submit filtered values to the server
   * @param {string} filteredValues The filtered values JSON string
   * @param {string} version The version ID
   * @returns {Promise<Object>} The response from the server
   */
  async submitFilteredValues(filteredValues, version) {
    try {
      // Extract numeric version from version ID (e.g., 'v1' -> '1')
      const numericVersion = version.replace(/\D/g, '');
      
      // Submit to the complete set endpoint
      const response = await fetch(this.submitCompleteSetUrl + numericVersion, {
        method: 'POST',
        headers: {
          'Content-Type': 'text/plain'
        },
        body: filteredValues
      });
      
      if (!response.ok) {
        throw new Error(`Failed to submit filtered values: ${response.statusText}`);
      }
      
      return await response.text();
    } catch (error) {
      console.error('Error submitting filtered values:', error);
      throw error;
    }
  }

  /**
   * Run the formatter module
   * @param {string} version The version ID
   * @returns {Promise<Object>} The response from the server
   */
  async runFormatter(version) {
    try {
      // Extract numeric version from version ID
      const numericVersion = version.replace(/\D/g, '');
      
      const response = await fetch(this.formatterUrl + numericVersion, {
        method: 'GET'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to run formatter: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error running formatter:', error);
      throw error;
    }
  }

  /**
   * Run module1 to build the configuration matrix
   * @param {string} version The version ID
   * @returns {Promise<Object>} The response from the server
   */
  async runModule1(version) {
    try {
      // Extract numeric version from version ID
      const numericVersion = version.replace(/\D/g, '');
      
      const response = await fetch(this.module1Url + numericVersion, {
        method: 'GET'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to run module1: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error running module1:', error);
      throw error;
    }
  }

  /**
   * Run config_modules to create configuration modules
   * @param {string} version The version ID
   * @returns {Promise<Object>} The response from the server
   */
  async runConfigModules(version) {
    try {
      // Extract numeric version from version ID
      const numericVersion = version.replace(/\D/g, '');
      
      const response = await fetch(this.configModulesUrl + numericVersion, {
        method: 'GET'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to run config_modules: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error running config_modules:', error);
      throw error;
    }
  }

  /**
   * Run table module to create the variable table
   * @param {string} version The version ID
   * @returns {Promise<Object>} The response from the server
   */
  async runTable(version) {
    try {
      // Extract numeric version from version ID
      const numericVersion = version.replace(/\D/g, '');
      
      const response = await fetch(this.tableUrl + numericVersion, {
        method: 'GET'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to run table module: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error running table module:', error);
      throw error;
    }
  }
}

export default MatrixSubmissionService;
