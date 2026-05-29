/**
 * Utility functions for component metadata
 */

import type { ComponentMetadata, ComponentCategory, PropSchema } from './index';

/**
 * Create default metadata for a component
 */
export function createDefaultMetadata(
  name: string,
  category?: ComponentCategory
): ComponentMetadata {
  return {
    type: name,
    label: formatLabel(name),
    comment: `${formatLabel(name)} component`,
    keywords: [name, formatLabel(name)],
    category: category ?? inferCategory(name),
    propSchema: {}
  };
}

/**
 * Format component name to human-readable label
 * e.g., "EmailInput" -> "Email Input"
 */
export function formatLabel(name: string): string {
  return name
    .replace(/([A-Z])/g, ' $1')
    .trim()
    .replace(/^./, (c) => c.toUpperCase());
}

/**
 * Infer component category from name
 */
export function inferCategory(name: string): ComponentCategory {
  const lowerName = name.toLowerCase();
  
  if (lowerName.includes('card') || lowerName.includes('board') || lowerName.includes('list')) {
    return 'Organism';
  }
  if (lowerName.includes('field') || lowerName.includes('group') || lowerName.includes('form')) {
    return 'Molecule';
  }
  if (lowerName.includes('input') || lowerName.includes('button') || lowerName.includes('label') || lowerName.includes('icon')) {
    return 'Atom';
  }
  if (lowerName.includes('template') || lowerName.includes('layout') || lowerName.includes('page')) {
    return 'Template';
  }
  
  return 'Container';
}

/**
 * Validate metadata structure
 */
export function validateMetadata(metadata: ComponentMetadata): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  if (!metadata.type) {
    errors.push('Missing required field: type');
  }
  if (!metadata.label) {
    errors.push('Missing required field: label');
  }
  if (!metadata.comment) {
    errors.push('Missing required field: comment');
  }
  if (!metadata.keywords || metadata.keywords.length === 0) {
    errors.push('Missing required field: keywords (must have at least one)');
  }
  if (!metadata.category) {
    errors.push('Missing required field: category');
  }
  if (!metadata.propSchema) {
    errors.push('Missing required field: propSchema');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Merge existing metadata with new/default values
 * Existing values take precedence
 */
export function mergeMetadata(
  existing: Partial<ComponentMetadata>,
  defaults: ComponentMetadata
): ComponentMetadata {
  return {
    ...defaults,
    ...existing,
    // Merge arrays instead of overwriting
    keywords: [...new Set([...(existing.keywords ?? []), ...defaults.keywords])],
    hasPart: existing.hasPart ?? defaults.hasPart,
    requires: existing.requires ?? defaults.requires,
    // Merge propSchema
    propSchema: {
      ...defaults.propSchema,
      ...existing.propSchema
    }
  };
}

/**
 * Convert extracted props to PropSchema
 */
export function propsToSchema(props: Array<{ name: string; type: string; defaultValue?: string; required: boolean }>): PropSchema {
  const schema: PropSchema = {};
  
  for (const prop of props) {
    schema[prop.name] = {
      type: prop.type,
      default: prop.defaultValue,
      required: prop.required
    };
  }
  
  return schema;
}
