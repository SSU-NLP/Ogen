/**
 * 디자인 시스템 컴포넌트 정보를 TTL 형식으로 변환하는 유틸리티
 * 
 * 이 함수는 라이브러리에 있어야 하며, 데모 앱에서는 import하여 사용합니다.
 */

export interface ComponentMetadata {
    // 기본 정보
    type: string;
    label: string;
    comment: string;
    keywords: string[];
    
    // 분류
    category: 'Atom' | 'Molecule' | 'Organism' | 'Template' | 'Container';
    
    // 관계
    hasPart?: string[];
    requires?: string[];
    conflictsWith?: string[];
    recommends?: string[];
    dependsOn?: string[];
    
    // 속성 스키마
    propSchema: {
        [key: string]: {
            type: string;
            default?: any;
            required?: boolean;
            description?: string;
            enum?: any[];
        };
    };
    
    // 기타 속성
    propType?: string;
    stylePreset?: string;
    
    // 검증
    validationRules?: {
        pattern?: string;
        minLength?: number;
        maxLength?: number;
        message?: string;
        [key: string]: any;
    };
    required?: boolean;
    
    // 레이아웃
    layoutType?: 'flex' | 'grid' | 'block' | 'inline';
    flexDirection?: 'row' | 'column';
    spacing?: string;
    alignment?: string;
    
    // 접근성
    ariaLabel?: string;
    role?: string;
    ariaDescribedBy?: string;
    ariaRequired?: boolean;
    
    // 상태
    defaultState?: string;
    loadingState?: boolean;
    disabledState?: boolean;
    
    // 스타일
    variant?: string;
    size?: string;
    theme?: string;
}

export function generateTTLFromDesignSystem(
    components: Record<string, any>,
    metadataMap?: Record<string, ComponentMetadata>,
    baseIRI: string = "http://myapp.com/ui/",
    ontologyPrefix: string = "http://ogen.ai/ontology/"
): string {
    const lines: string[] = [];
    
    // Prefixes
    lines.push(`@prefix user: <${baseIRI}> .`);
    lines.push(`@prefix ogen: <${ontologyPrefix}> .`);
    lines.push(`@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .`);
    lines.push(`@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .`);
    lines.push(`@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .`);
    lines.push('');
    
    // 각 컴포넌트를 TTL로 변환
    for (const [componentName, component] of Object.entries(components)) {
        if (componentName === 'default') continue;
        
        // 메타데이터가 있으면 우선 사용, 없으면 추론
        let metadata: ComponentMetadata;
        if (metadataMap && metadataMap[componentName]) {
            metadata = metadataMap[componentName];
        } else {
            // 하위 호환성: 기존 추론 방식 유지
            metadata = extractMetadata(componentName, component);
        }
        
        const ttl = generateComponentTTL(componentName, metadata, baseIRI, ontologyPrefix);
        lines.push(ttl);
        lines.push('');
    }
    
    return lines.join('\n');
}

function extractMetadata(name: string, component: any): ComponentMetadata {
    // 기본 메타데이터 추출 (하위 호환성을 위한 추론 방식)
    const label = formatLabel(name);
    const category = inferCategory(name);
    
    const metadata: ComponentMetadata = {
        type: name,
        label: label,
        comment: `${label} component`,
        keywords: [name, label],
        category: category,
        propSchema: {}
    };
    
    return metadata;
}

function formatLabel(name: string): string {
    // PascalCase를 읽기 쉬운 형태로 변환
    return name
        .replace(/([A-Z])/g, ' $1')
        .trim()
        .replace(/^./, (c) => c.toUpperCase());
}

function inferCategory(name: string): ComponentMetadata['category'] {
    // 이름 기반으로 카테고리 추론
    const lowerName = name.toLowerCase();
    
    if (lowerName.includes('card') || lowerName.includes('board') || lowerName.includes('container')) {
        return 'Organism';
    }
    if (lowerName.includes('field') || lowerName.includes('group')) {
        return 'Molecule';
    }
    if (lowerName.includes('input') || lowerName.includes('button') || lowerName.includes('label')) {
        return 'Atom';
    }
    
    return 'Container';
}

function generateComponentTTL(
    name: string,
    metadata: ComponentMetadata,
    baseIRI: string,
    ontologyPrefix: string
): string {
    const lines: string[] = [];
    const category = metadata.category || 'Container';
    
    // 기본 타입 선언
    lines.push(`user:${name} a ogen:${category} ;`);
    
    // Label
    if (metadata.label) {
        lines.push(`    rdfs:label "${escapeString(metadata.label)}" ;`);
    }
    
    // Comment
    if (metadata.comment) {
        lines.push(`    rdfs:comment "${escapeString(metadata.comment)}" ;`);
    }
    
    // Keywords (배열을 문자열로 변환)
    if (metadata.keywords && metadata.keywords.length > 0) {
        const keywordsStr = metadata.keywords.join(', ');
        lines.push(`    ogen:keywords "${escapeString(keywordsStr)}" ;`);
    }
    
    // HasPart
    if (metadata.hasPart && metadata.hasPart.length > 0) {
        const parts = metadata.hasPart.map(p => `user:${p}`).join(', ');
        lines.push(`    ogen:hasPart ${parts} ;`);
    }
    
    // Requires
    if (metadata.requires && metadata.requires.length > 0) {
        const requires = metadata.requires.map(r => `user:${r}`).join(', ');
        lines.push(`    ogen:requires ${requires} ;`);
    }
    
    // ConflictsWith
    if (metadata.conflictsWith && metadata.conflictsWith.length > 0) {
        const conflicts = metadata.conflictsWith.map(c => `user:${c}`).join(', ');
        lines.push(`    ogen:conflictsWith ${conflicts} ;`);
    }
    
    // Recommends
    if (metadata.recommends && metadata.recommends.length > 0) {
        const recommends = metadata.recommends.map(r => `user:${r}`).join(', ');
        lines.push(`    ogen:recommends ${recommends} ;`);
    }
    
    // DependsOn
    if (metadata.dependsOn && metadata.dependsOn.length > 0) {
        const depends = metadata.dependsOn.map(d => `user:${d}`).join(', ');
        lines.push(`    ogen:dependsOn ${depends} ;`);
    }
    
    // PropSchema
    if (metadata.propSchema && Object.keys(metadata.propSchema).length > 0) {
        const schemaJson = JSON.stringify(metadata.propSchema).replace(/"/g, '\\"');
        lines.push(`    ogen:propSchema """${schemaJson}""" ;`);
    }
    
    // PropType
    if (metadata.propType) {
        lines.push(`    ogen:propType "${escapeString(metadata.propType)}" ;`);
    }
    
    // StylePreset
    if (metadata.stylePreset) {
        lines.push(`    ogen:stylePreset "${escapeString(metadata.stylePreset)}" ;`);
    }
    
    // ValidationRules
    if (metadata.validationRules && Object.keys(metadata.validationRules).length > 0) {
        const validationJson = JSON.stringify(metadata.validationRules).replace(/"/g, '\\"');
        lines.push(`    ogen:validationRules """${validationJson}""" ;`);
    }
    
    // Required
    if (metadata.required !== undefined) {
        lines.push(`    ogen:required "${metadata.required}"^^xsd:boolean ;`);
    }
    
    // MinLength
    if (metadata.validationRules?.minLength !== undefined) {
        lines.push(`    ogen:minLength "${metadata.validationRules.minLength}"^^xsd:integer ;`);
    }
    
    // MaxLength
    if (metadata.validationRules?.maxLength !== undefined) {
        lines.push(`    ogen:maxLength "${metadata.validationRules.maxLength}"^^xsd:integer ;`);
    }
    
    // Pattern
    if (metadata.validationRules?.pattern) {
        lines.push(`    ogen:pattern "${escapeString(metadata.validationRules.pattern)}" ;`);
    }
    
    // LayoutType
    if (metadata.layoutType) {
        lines.push(`    ogen:layoutType "${metadata.layoutType}" ;`);
    }
    
    // FlexDirection
    if (metadata.flexDirection) {
        lines.push(`    ogen:flexDirection "${metadata.flexDirection}" ;`);
    }
    
    // Spacing
    if (metadata.spacing) {
        lines.push(`    ogen:spacing "${escapeString(metadata.spacing)}" ;`);
    }
    
    // Alignment
    if (metadata.alignment) {
        lines.push(`    ogen:alignment "${metadata.alignment}" ;`);
    }
    
    // AriaLabel
    if (metadata.ariaLabel) {
        lines.push(`    ogen:ariaLabel "${escapeString(metadata.ariaLabel)}" ;`);
    }
    
    // Role
    if (metadata.role) {
        lines.push(`    ogen:role "${metadata.role}" ;`);
    }
    
    // AriaDescribedBy
    if (metadata.ariaDescribedBy) {
        lines.push(`    ogen:ariaDescribedBy "${escapeString(metadata.ariaDescribedBy)}" ;`);
    }
    
    // AriaRequired
    if (metadata.ariaRequired !== undefined) {
        lines.push(`    ogen:ariaRequired "${metadata.ariaRequired}"^^xsd:boolean ;`);
    }
    
    // DefaultState
    if (metadata.defaultState) {
        lines.push(`    ogen:defaultState "${metadata.defaultState}" ;`);
    }
    
    // LoadingState
    if (metadata.loadingState !== undefined) {
        lines.push(`    ogen:loadingState "${metadata.loadingState}"^^xsd:boolean ;`);
    }
    
    // DisabledState
    if (metadata.disabledState !== undefined) {
        lines.push(`    ogen:disabledState "${metadata.disabledState}"^^xsd:boolean ;`);
    }
    
    // Variant
    if (metadata.variant) {
        lines.push(`    ogen:variant "${metadata.variant}" ;`);
    }
    
    // Size
    if (metadata.size) {
        lines.push(`    ogen:size "${metadata.size}" ;`);
    }
    
    // Theme
    if (metadata.theme) {
        lines.push(`    ogen:theme "${metadata.theme}" ;`);
    }
    
    // 마지막 세미콜론 제거하고 마침표 추가
    if (lines.length > 1) {
        const lastLine = lines[lines.length - 1];
        lines[lines.length - 1] = lastLine.replace(/ ;$/, ' .');
    } else {
        lines[lines.length - 1] = lines[lines.length - 1].replace(/ ;$/, ' .');
    }
    
    return lines.join('\n');
}

function escapeString(str: string): string {
    return str.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
}

