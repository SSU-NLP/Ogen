/**
 * Type definitions for @ogen/design-studio
 */

// ===== Component Category =====
export type ComponentCategory = 'Atom' | 'Molecule' | 'Organism' | 'Template' | 'Container';

// ===== Property Schema =====
export interface PropSchema {
  [key: string]: {
    type: string;
    default?: unknown;
    required?: boolean;
    description?: string;
    enum?: unknown[];
  };
}

// ===== Validation Rules =====
export interface ValidationRules {
  pattern?: string;
  minLength?: number;
  maxLength?: number;
  min?: number;
  max?: number;
  message?: string;
  [key: string]: unknown;
}

// ===== Ontology Relation =====
export interface OntologyRelation {
  type: 'hasPart' | 'requires' | 'conflictsWith' | 'recommends' | 'dependsOn';
  target: string;
  description?: string;
}

// ===== Component Metadata =====
export interface ComponentMetadata {
  // Basic info
  type: string;
  label: string;
  comment: string;
  keywords: string[];
  
  // Classification
  category: ComponentCategory;
  
  // Ontology relations
  hasPart?: string[];
  requires?: string[];
  conflictsWith?: string[];
  recommends?: string[];
  dependsOn?: string[];
  
  // Property schema
  propSchema: PropSchema;
  
  // Additional properties
  propType?: string;
  stylePreset?: string;
  
  // Validation
  validationRules?: ValidationRules;
  required?: boolean;
  
  // Layout
  layoutType?: 'flex' | 'grid' | 'block' | 'inline';
  flexDirection?: 'row' | 'column';
  spacing?: string;
  alignment?: string;
  
  // Accessibility
  ariaLabel?: string;
  role?: string;
  ariaDescribedBy?: string;
  ariaRequired?: boolean;
  
  // State
  defaultState?: string;
  loadingState?: boolean;
  disabledState?: boolean;
  
  // Style
  variant?: string;
  size?: string;
  theme?: string;
}

// ===== Component Info (from scan) =====
export interface ComponentInfo {
  name: string;
  path: string;
  filename: string;
  props: ExtractedProp[];
  hasScript: boolean;
  hasStyle: boolean;
  rawContent?: string;
}

export interface ExtractedProp {
  name: string;
  type: string;
  defaultValue?: string;
  required: boolean;
}

// ===== Scan Options =====
export interface ScanOptions {
  /** Directory to scan */
  directory: string;
  /** File extensions to include (default: ['.svelte']) */
  extensions?: string[];
  /** Whether to include subdirectories (default: true) */
  recursive?: boolean;
  /** Existing metadata to merge with */
  existingMetadata?: Record<string, ComponentMetadata>;
  /** Base IRI for TTL generation */
  baseIRI?: string;
}

// ===== Scan Result =====
export interface ScanResult {
  /** Scanned components */
  components: ComponentInfo[];
  /** Generated/merged metadata */
  metadata: Record<string, ComponentMetadata>;
  /** Scan timestamp */
  scannedAt: Date;
  /** Source directory */
  directory: string;
  /** Any errors encountered */
  errors: ScanError[];
}

export interface ScanError {
  file: string;
  message: string;
  line?: number;
}

// ===== TTL Generation Options =====
export interface TTLGenerationOptions {
  baseIRI?: string;
  ontologyPrefix?: string;
  includeComments?: boolean;
  prettyPrint?: boolean;
}

// ===== Design Studio State =====
export interface DesignStudioState {
  components: ComponentInfo[];
  metadata: Record<string, ComponentMetadata>;
  selectedComponent: string | null;
  isDirty: boolean;
  lastSaved: Date | null;
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error';
}

// ===== Event Types =====
export interface MetadataChangeEvent {
  componentName: string;
  field: keyof ComponentMetadata;
  oldValue: unknown;
  newValue: unknown;
}

export interface SaveEvent {
  metadata: Record<string, ComponentMetadata>;
  ttl: string;
  timestamp: Date;
}

// ===== Preview / Stories =====
export interface StoryVariant {
  name: string;
  props: Record<string, unknown>;
  /** Optional default slot text for preview */
  slotText?: string;
}

export type StoryMap = Record<string, StoryVariant[]>;

export type ComponentRegistry = Record<string, any>;

export interface FilePersistencePayload {
  metadata: Record<string, ComponentMetadata>;
}
