/**
 * TTL Generator
 * 
 * Converts component metadata to TTL (Turtle) format for RDF/ontology
 */

import type { ComponentMetadata, TTLGenerationOptions } from '../types';
import { createDefaultMetadata } from '../types/utils';

/** Atomic-Design / ontology classes that are valid rdf:type values. */
const VALID_CATEGORIES = new Set([
  'Atom',
  'Molecule',
  'Organism',
  'Template',
  'Container',
  'Action',
]);

/**
 * A Turtle prefixed-name local part must be a safe token. We allow the common
 * component-id subset; anything else (spaces, quotes, punctuation) would
 * produce invalid Turtle and break the whole graph parse, so it is rejected.
 */
function isValidLocalName(name: unknown): name is string {
  return typeof name === 'string' && /^[A-Za-z_][A-Za-z0-9_-]*$/.test(name);
}

/**
 * Generate TTL from metadata map
 * 
 * @example
 * ```ts
 * const ttl = generateTTL(metadata, {
 *   baseIRI: 'http://myapp.com/ui/',
 *   ontologyPrefix: 'http://ogen.ai/ontology/'
 * });
 * ```
 */
export function generateTTL(
  metadata: Record<string, ComponentMetadata>,
  options: TTLGenerationOptions = {},
  warnings: string[] = []
): string {
  const {
    baseIRI = 'http://myapp.com/ui/',
    ontologyPrefix = 'http://ogen.ai/ontology/',
    includeComments = true,
    prettyPrint = true
  } = options;

  const lines: string[] = [];
  const nl = prettyPrint ? '\n' : ' ';

  // Prefixes
  lines.push(`@prefix user: <${baseIRI}> .`);
  lines.push(`@prefix ogen: <${ontologyPrefix}> .`);
  lines.push(`@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .`);
  lines.push(`@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .`);
  lines.push(`@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .`);
  lines.push('');

  // Generate TTL for each component
  for (const [name, meta] of Object.entries(metadata)) {
    const componentTTL = generateComponentTTL(name, meta, baseIRI, ontologyPrefix, warnings);
    if (!componentTTL) continue; // skipped (invalid name) — already warned
    if (includeComments) {
      lines.push(`# ${meta.label ?? name}`);
    }
    lines.push(componentTTL);
    lines.push('');
  }

  return lines.join(nl);
}

/**
 * Generate TTL for a component registry.
 *
 * - Includes ONLY components present in registryKeys.
 * - If metadata is missing for a component, uses minimal defaults.
 * - Excludes metadata-only nodes ("red") by design.
 */
export function generateTTLForRegistry(
  registryKeys: string[],
  metadata: Record<string, ComponentMetadata>,
  options: TTLGenerationOptions = {},
  warnings: string[] = []
): string {
  const {
    baseIRI = 'http://myapp.com/ui/',
    ontologyPrefix = 'http://ogen.ai/ontology/',
    includeComments = true,
    prettyPrint = true
  } = options;

  const lines: string[] = [];
  const nl = prettyPrint ? '\n' : ' ';

  lines.push(`@prefix user: <${baseIRI}> .`);
  lines.push(`@prefix ogen: <${ontologyPrefix}> .`);
  lines.push(`@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .`);
  lines.push(`@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .`);
  lines.push(`@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .`);
  lines.push('');

  for (const name of registryKeys) {
    if (name === 'default') continue;
    const meta = metadata[name] ?? createDefaultMetadata(name);
    if (!meta.propSchema) {
      meta.propSchema = {};
    }
    const componentTTL = generateComponentTTL(name, meta, baseIRI, ontologyPrefix, warnings);
    if (!componentTTL) continue; // skipped (invalid name) — already warned
    if (includeComments) {
      lines.push(`# ${meta.label ?? name}`);
    }
    lines.push(componentTTL);
    lines.push('');
  }

  return lines.join(nl);
}

/**
 * Generate TTL for a single component
 */
export function generateComponentTTL(
  name: string,
  metadata: ComponentMetadata,
  baseIRI: string = 'http://myapp.com/ui/',
  ontologyPrefix: string = 'http://ogen.ai/ontology/',
  warnings: string[] = []
): string {
  // A node with an invalid local name cannot be expressed as a valid IRI;
  // emitting it would break the entire graph parse, so skip it.
  if (!isValidLocalName(name)) {
    warnings.push(`Skipped component "${name}": invalid name (must match [A-Za-z_][A-Za-z0-9_-]*).`);
    return '';
  }

  const lines: string[] = [];

  // Component declaration. Guard the category so we never emit `a ogen: ;`.
  let category = metadata.category as string;
  if (!VALID_CATEGORIES.has(category)) {
    warnings.push(`Component "${name}": invalid/missing category "${category ?? ''}", defaulting to Atom.`);
    category = 'Atom';
  }
  lines.push(`user:${name} a ogen:${category} ;`);

  // Basic info (always escaped)
  lines.push(`    rdfs:label "${escapeString(metadata.label ?? name)}" ;`);
  lines.push(`    rdfs:comment "${escapeString(metadata.comment ?? '')}" ;`);

  // Keywords
  if (metadata.keywords && metadata.keywords.length > 0) {
    const keywords = metadata.keywords.map(k => escapeString(k)).join(', ');
    lines.push(`    ogen:keywords "${keywords}" ;`);
  }

  // Ontology relations — skip invalid targets instead of breaking the graph.
  const emitRelation = (predicate: string, targets: string[] | undefined) => {
    if (!targets || targets.length === 0) return;
    for (const target of targets) {
      if (!isValidLocalName(target)) {
        warnings.push(`Component "${name}": skipped ${predicate} target "${target}" (invalid name).`);
        continue;
      }
      lines.push(`    ogen:${predicate} user:${target} ;`);
    }
  };
  emitRelation('hasPart', metadata.hasPart);
  emitRelation('requires', metadata.requires);
  emitRelation('conflictsWith', metadata.conflictsWith);
  emitRelation('recommends', metadata.recommends);
  emitRelation('dependsOn', metadata.dependsOn);

  // Property schema as JSON — escape the JSON and embed as a normal string
  // literal. (A """long string""" still processes \n / \" / \uXXXX escapes,
  // which would corrupt the JSON on the backend's json.loads.)
  if (metadata.propSchema && Object.keys(metadata.propSchema).length > 0) {
    const propsJson = JSON.stringify(metadata.propSchema);
    lines.push(`    ogen:propSchema "${escapeString(propsJson)}"^^xsd:string ;`);
  }

  // Layout (escaped)
  if (metadata.layoutType) {
    lines.push(`    ogen:layoutType "${escapeString(metadata.layoutType)}" ;`);
  }
  if (metadata.flexDirection) {
    lines.push(`    ogen:flexDirection "${escapeString(metadata.flexDirection)}" ;`);
  }
  if (metadata.spacing) {
    lines.push(`    ogen:spacing "${escapeString(metadata.spacing)}" ;`);
  }

  // Accessibility (escaped)
  if (metadata.ariaLabel) {
    lines.push(`    ogen:ariaLabel "${escapeString(metadata.ariaLabel)}" ;`);
  }
  if (metadata.role) {
    lines.push(`    ogen:role "${escapeString(metadata.role)}" ;`);
  }

  // State (escaped)
  if (metadata.defaultState) {
    lines.push(`    ogen:defaultState "${escapeString(metadata.defaultState)}" ;`);
  }

  // Style (escaped)
  if (metadata.variant) {
    lines.push(`    ogen:variant "${escapeString(metadata.variant)}" ;`);
  }

  // Validation rules as JSON (escaped, normal literal)
  if (metadata.validationRules && Object.keys(metadata.validationRules).length > 0) {
    const rulesJson = JSON.stringify(metadata.validationRules);
    lines.push(`    ogen:validationRules "${escapeString(rulesJson)}"^^xsd:string ;`);
  }

  // Close the statement (replace last ; with .)
  const lastLine = lines[lines.length - 1];
  lines[lines.length - 1] = lastLine.replace(/\s*;$/, ' .');

  return lines.join('\n');
}

/**
 * Serialize metadata to TTL string (alias for generateTTL)
 */
export function serializeToTTL(
  metadata: Record<string, ComponentMetadata>,
  options?: TTLGenerationOptions
): string {
  return generateTTL(metadata, options);
}

/**
 * Escape special characters in string for TTL
 */
function escapeString(str: string): string {
  return String(str ?? '')
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '\\r')
    .replace(/\t/g, '\\t');
}

/**
 * Parse TTL back to metadata (basic parser)
 * Note: This is a simplified parser for our specific TTL format
 */
export function parseTTL(ttl: string): Record<string, Partial<ComponentMetadata>> {
  const metadata: Record<string, Partial<ComponentMetadata>> = {};
  
  // Match component blocks
  const componentRegex = /user:(\w+)\s+a\s+ogen:(\w+)\s*;([^.]+)\./g;
  
  let match;
  while ((match = componentRegex.exec(ttl)) !== null) {
    const [, name, category, properties] = match;
    
    const meta: Partial<ComponentMetadata> = {
      type: name,
      category: category as ComponentMetadata['category']
    };
    
    // Extract label
    const labelMatch = properties.match(/rdfs:label\s+"([^"]+)"/);
    if (labelMatch) meta.label = labelMatch[1];
    
    // Extract comment
    const commentMatch = properties.match(/rdfs:comment\s+"([^"]+)"/);
    if (commentMatch) meta.comment = commentMatch[1];
    
    // Extract keywords
    const keywordsMatch = properties.match(/ogen:keywords\s+"([^"]+)"/);
    if (keywordsMatch) {
      meta.keywords = keywordsMatch[1].split(',').map(k => k.trim());
    }
    
    metadata[name] = meta;
  }
  
  return metadata;
}
