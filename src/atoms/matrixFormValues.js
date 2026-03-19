/**
 * matrixFormValues.js
 *
 * Jotai atoms for the version-centric model.
 * Zone atoms removed — zone is no longer part of the core model.
 */

import { atomWithStorage } from 'jotai/utils';

// Clean up any stale zone data from localStorage
if (typeof window !== 'undefined') {
  localStorage.removeItem('tea-zones');
}

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
