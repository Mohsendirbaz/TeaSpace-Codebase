import React from 'react';
import FactualPrecedenceBase from './FactualPrecedenceBase';
import { getPrePopulatedPrecedenceData } from '../../../data/factualPrecedenceData';

const LocalFactualPrecedence = (props) => {
  return (
    <FactualPrecedenceBase
      {...props}
      getPrecedenceData={getPrePopulatedPrecedenceData}
    />
  );
};

export default LocalFactualPrecedence;
