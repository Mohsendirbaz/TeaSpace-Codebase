/**
 * matrixFormValues.js
 *
 * Jotai atoms whose shapes mirror the React useState initializers in
 * useMatrixFormValues (src/Consolidated2.js lines 21-44).
 *
 * The tooltip reads these atoms to display the active version/zone label.
 * Any component that changes versions/zones via useMatrixFormValues should
 * also write the updated value here so the tooltip stays in sync.
 */

import { atom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';

// Matches exactly the initial state set in useMatrixFormValues (Consolidated2.js:21-32)
export const versionsAtom = atomWithStorage('tea-versions', {
  list: ['v1'],
  active: 'v1',
  metadata: {
    v1: {
      label: 'Base Case',
      description: 'Default financial case',
      created: Date.now(),
      modified: Date.now(),
    },
  },
});

// Matches exactly the initial state set in useMatrixFormValues (Consolidated2.js:34-44)
export const zonesAtom = atomWithStorage('tea-zones', {
  list: ['z1'],
  active: 'z1',
  metadata: {
    z1: {
      label: 'Local',
      description: 'Local market zone',
      created: Date.now(),
    },
  },
});
