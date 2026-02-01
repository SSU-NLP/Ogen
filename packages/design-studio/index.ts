/**
 * @ogen/design-studio
 * 
 * Design system management tool for Ogen UI
 * - Scan component directories
 * - Edit component metadata
 * - Generate TTL ontology files
 * - Sync with backend
 */

// Types
export type {
  ComponentMetadata,
  PropSchema,
  ValidationRules,
  ScanResult,
  ScanOptions,
  ComponentInfo,
  OntologyRelation,
  StoryVariant,
  StoryMap,
  ComponentRegistry
} from './types';

// Scanner
export {
  scanComponents,
  scanDirectory,
  extractMetadataFromComponent,
  scanFromFileList
} from './scanner';

// Generator
export {
  generateTTL,
  generateTTLForRegistry,
  generateComponentTTL,
  serializeToTTL
} from './generator';

// Editor UI Components
export {
  DesignStudioUI,
  ComponentPreview,
  OntologyGraph
} from './editor';

// Utilities
export {
  createDefaultMetadata,
  validateMetadata,
  mergeMetadata
} from './types/utils';
