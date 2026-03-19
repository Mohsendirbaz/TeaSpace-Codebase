import React from 'react';
import LocalFactualPrecedence from './LocalFactualPrecedence';
import APIFactualPrecedence from './APIFactualPrecedence';
import FilteredFactualPrecedence from './FilteredFactualPrecedence';

const FactualPrecedence = (props) => {
  // Configuration variables
  const implementationType = process.env.REACT_APP_FACTUAL_PRECEDENCE_TYPE || 'local';
  
  switch (implementationType) {
    case 'api':
      return <APIFactualPrecedence {...props} />;
    case 'filtered':
      return <FilteredFactualPrecedence {...props} />;
    case 'local':
    default:
      return <LocalFactualPrecedence {...props} />;
  }
};

export default FactualPrecedence;
