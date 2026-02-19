import Alert from './components/Alert.svelte';
import Avatar from './components/Avatar.svelte';
import Badge from './components/Badge.svelte';
import Breadcrumbs from './components/Breadcrumbs.svelte';
import Button from './components/Button.svelte';
import Card from './components/Card.svelte';
import Checkbox from './components/Checkbox.svelte';
import CheckboxGroup from './components/CheckboxGroup.svelte';
import Chip from './components/Chip.svelte';
import Container from './components/Container.svelte';
import DatePicker from './components/DatePicker.svelte';
import Divider from './components/Divider.svelte';
import EmailField from './components/EmailField.svelte';
import EmptyState from './components/EmptyState.svelte';
import Footer from './components/Footer.svelte';
import FormField from './components/FormField.svelte';
import Heading from './components/Heading.svelte';
import HeroSection from './components/HeroSection.svelte';
import Icon from './components/Icon.svelte';
import IconButton from './components/IconButton.svelte';
import Image from './components/Image.svelte';
import Input from './components/Input.svelte';
import InputGroup from './components/InputGroup.svelte';
import Label from './components/Label.svelte';
import Link from './components/Link.svelte';
import List from './components/List.svelte';
import Modal from './components/Modal.svelte';
import Pagination from './components/Pagination.svelte';
import PasswordField from './components/PasswordField.svelte';
import ProgressBar from './components/ProgressBar.svelte';
import Radio from './components/Radio.svelte';
import RadioGroup from './components/RadioGroup.svelte';
import SearchBar from './components/SearchBar.svelte';
import SearchField from './components/SearchField.svelte';
import Select from './components/Select.svelte';
import SelectField from './components/SelectField.svelte';
import SideNav from './components/SideNav.svelte';
import Slider from './components/Slider.svelte';
import Spinner from './components/Spinner.svelte';
import StatCard from './components/StatCard.svelte';
import StatusDot from './components/StatusDot.svelte';
import Table from './components/Table.svelte';
import Tabs from './components/Tabs.svelte';
import Tag from './components/Tag.svelte';
import Text from './components/Text.svelte';
import Textarea from './components/Textarea.svelte';
import ToggleField from './components/ToggleField.svelte';
import ToggleSwitch from './components/ToggleSwitch.svelte';
import Toolbar from './components/Toolbar.svelte';
import Tooltip from './components/Tooltip.svelte';
import TopNav from './components/TopNav.svelte';
import type { ComponentMetadata } from '@ogen/svelte';

export const designSystem: Record<string, any> = {
  LoginCard: Container,
  TodoList: Container,
  KanbanBoard: Container,
  Molecule: Container,
  EmailInput: Input,
  PasswordInput: Input,
  SearchInput: Input,
  TodoInput: Input,
  SubmitButton: Button,
  SearchIcon: Icon,

  Alert,
  Avatar,
  Badge,
  Breadcrumbs,
  Button,
  Card,
  Checkbox,
  CheckboxGroup,
  Chip,
  Container,
  DatePicker,
  Divider,
  EmailField,
  EmptyState,
  Footer,
  FormField,
  Heading,
  HeroSection,
  Icon,
  IconButton,
  Image,
  Input,
  InputGroup,
  Label,
  Link,
  List,
  Modal,
  Pagination,
  PasswordField,
  ProgressBar,
  Radio,
  RadioGroup,
  SearchBar,
  SearchField,
  Select,
  SelectField,
  SideNav,
  Slider,
  Spinner,
  StatCard,
  StatusDot,
  Table,
  Tabs,
  Tag,
  Text,
  Textarea,
  ToggleField,
  ToggleSwitch,
  Toolbar,
  Tooltip,
  TopNav,

  default: Container
};

export const designSystemMetadata: Record<string, ComponentMetadata> = {
  LoginCard: {
    type: 'LoginCard',
    label: 'Login Card',
    comment: 'Authentication container with email, password, and submit.',
    keywords: ['login', 'auth', 'card', 'form'],
    category: 'Organism',
    hasPart: ['EmailField', 'PasswordField', 'SubmitButton'],
    propSchema: {
      label: { type: 'string', default: 'Login', description: 'Card title' },
      style: { type: 'string', default: '', description: 'Inline styles' }
    }
  },
  TodoList: {
    type: 'TodoList',
    label: 'Todo List',
    comment: 'List container for tasks.',
    keywords: ['todo', 'list', 'tasks'],
    category: 'Organism',
    hasPart: ['List'],
    propSchema: {
      label: { type: 'string', default: 'Tasks', description: 'Section title' },
      style: { type: 'string', default: '', description: 'Inline styles' }
    }
  },
  KanbanBoard: {
    type: 'KanbanBoard',
    label: 'Kanban Board',
    comment: 'Board container for columns.',
    keywords: ['kanban', 'board', 'workflow'],
    category: 'Organism',
    hasPart: ['Container'],
    propSchema: {
      label: { type: 'string', default: 'Board', description: 'Board title' },
      style: { type: 'string', default: '', description: 'Inline styles' }
    }
  },
  Molecule: {
    type: 'Molecule',
    label: 'Molecule',
    comment: 'Generic composite container.',
    keywords: ['composite', 'container'],
    category: 'Molecule',
    hasPart: ['Container'],
    propSchema: {
      label: { type: 'string', default: '', description: 'Section label' },
      style: { type: 'string', default: '', description: 'Inline styles' }
    }
  },
  EmailInput: {
    type: 'EmailInput',
    label: 'Email Input',
    comment: 'Input configured for email.',
    keywords: ['email', 'input', 'field'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: 'Email', description: 'Field label' },
      type: { type: 'string', default: 'email', description: 'Input type' },
      placeholder: { type: 'string', default: 'user@example.com', description: 'Placeholder' },
      id: { type: 'string', default: 'email', description: 'Input id' }
    }
  },
  PasswordInput: {
    type: 'PasswordInput',
    label: 'Password Input',
    comment: 'Input configured for password.',
    keywords: ['password', 'input', 'field'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: 'Password', description: 'Field label' },
      type: { type: 'string', default: 'password', description: 'Input type' },
      placeholder: { type: 'string', default: 'Enter password', description: 'Placeholder' },
      id: { type: 'string', default: 'password', description: 'Input id' }
    }
  },
  SearchInput: {
    type: 'SearchInput',
    label: 'Search Input',
    comment: 'Input configured for search.',
    keywords: ['search', 'input', 'field'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: 'Search', description: 'Field label' },
      type: { type: 'string', default: 'search', description: 'Input type' },
      placeholder: { type: 'string', default: 'Search', description: 'Placeholder' },
      id: { type: 'string', default: 'search', description: 'Input id' }
    }
  },
  TodoInput: {
    type: 'TodoInput',
    label: 'Todo Input',
    comment: 'Input for adding tasks.',
    keywords: ['todo', 'input', 'tasks'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: 'New task', description: 'Field label' },
      type: { type: 'string', default: 'text', description: 'Input type' },
      placeholder: { type: 'string', default: 'Add a task', description: 'Placeholder' },
      id: { type: 'string', default: 'todo', description: 'Input id' }
    }
  },
  SubmitButton: {
    type: 'SubmitButton',
    label: 'Submit Button',
    comment: 'Primary action button.',
    keywords: ['submit', 'button', 'cta'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: 'Submit', description: 'Button text' },
      variant: { type: 'string', default: 'primary', enum: ['primary', 'secondary'], description: 'Variant' }
    }
  },
  SearchIcon: {
    type: 'SearchIcon',
    label: 'Search Icon',
    comment: 'Search icon glyph.',
    keywords: ['icon', 'search'],
    category: 'Atom',
    propSchema: {
      name: { type: 'string', default: '🔍', description: 'Icon glyph' }
    }
  },

  Alert: {
    type: 'Alert',
    label: 'Alert',
    comment: 'Status or feedback message.',
    keywords: ['alert', 'status', 'message'],
    category: 'Molecule',
    propSchema: {
      tone: { type: 'string', default: 'info', enum: ['info', 'success', 'warning', 'danger'], description: 'Alert tone' },
      message: { type: 'string', default: 'Message', description: 'Alert text' }
    }
  },
  Avatar: {
    type: 'Avatar',
    label: 'Avatar',
    comment: 'User avatar image or initials.',
    keywords: ['avatar', 'user', 'profile'],
    category: 'Atom',
    propSchema: {
      name: { type: 'string', default: 'User', description: 'User name' },
      src: { type: 'string', default: '', description: 'Image URL' },
      size: { type: 'string', default: 'md', enum: ['sm', 'md', 'lg'], description: 'Avatar size' }
    }
  },
  Badge: {
    type: 'Badge',
    label: 'Badge',
    comment: 'Small status badge.',
    keywords: ['badge', 'status', 'label'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: 'Badge', description: 'Badge text' },
      tone: { type: 'string', default: 'neutral', enum: ['neutral', 'success', 'warning', 'danger'], description: 'Badge tone' }
    }
  },
  Breadcrumbs: {
    type: 'Breadcrumbs',
    label: 'Breadcrumbs',
    comment: 'Breadcrumb navigation list.',
    keywords: ['breadcrumbs', 'navigation', 'trail'],
    category: 'Molecule',
    propSchema: {
      items: { type: 'string[]', default: ['Home', 'Library'], description: 'Crumb labels' }
    }
  },
  Button: {
    type: 'Button',
    label: 'Button',
    comment: 'Clickable action button.',
    keywords: ['button', 'action', 'cta'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: 'Button', description: 'Button text' },
      variant: { type: 'string', default: 'primary', enum: ['primary', 'secondary'], description: 'Variant' }
    }
  },
  Card: {
    type: 'Card',
    label: 'Card',
    comment: 'Content card with title and subtitle.',
    keywords: ['card', 'content', 'panel'],
    category: 'Molecule',
    propSchema: {
      title: { type: 'string', default: 'Card title', description: 'Title text' },
      subtitle: { type: 'string', default: 'Subtitle', description: 'Subtitle text' }
    }
  },
  Checkbox: {
    type: 'Checkbox',
    label: 'Checkbox',
    comment: 'Single checkbox control.',
    keywords: ['checkbox', 'input', 'toggle'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: 'Option', description: 'Label text' },
      checked: { type: 'boolean', default: false, description: 'Checked state' }
    }
  },
  CheckboxGroup: {
    type: 'CheckboxGroup',
    label: 'Checkbox Group',
    comment: 'Group of checkbox options.',
    keywords: ['checkbox', 'group', 'options'],
    category: 'Molecule',
    propSchema: {
      options: { type: 'string[]', default: ['Option A', 'Option B'], description: 'Options list' }
    }
  },
  Chip: {
    type: 'Chip',
    label: 'Chip',
    comment: 'Compact label chip.',
    keywords: ['chip', 'label', 'tag'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: 'Chip', description: 'Chip text' }
    }
  },
  Container: {
    type: 'Container',
    label: 'Container',
    comment: 'Layout container with optional label.',
    keywords: ['container', 'layout', 'section'],
    category: 'Organism',
    propSchema: {
      label: { type: 'string', default: '', description: 'Section label' },
      style: { type: 'string', default: '', description: 'Inline styles' }
    }
  },
  DatePicker: {
    type: 'DatePicker',
    label: 'Date Picker',
    comment: 'Date input field.',
    keywords: ['date', 'picker', 'input'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: 'Date', description: 'Field label' }
    }
  },
  Divider: {
    type: 'Divider',
    label: 'Divider',
    comment: 'Section separator.',
    keywords: ['divider', 'separator', 'section'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: '', description: 'Optional label' }
    }
  },
  EmailField: {
    type: 'EmailField',
    label: 'Email Field',
    comment: 'Email input with label and placeholder.',
    keywords: ['email', 'input', 'field'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: 'Email', description: 'Field label' },
      placeholder: { type: 'string', default: 'user@example.com', description: 'Placeholder' }
    }
  },
  EmptyState: {
    type: 'EmptyState',
    label: 'Empty State',
    comment: 'Placeholder for empty content.',
    keywords: ['empty', 'placeholder', 'state'],
    category: 'Organism',
    propSchema: {
      title: { type: 'string', default: 'No data', description: 'Title text' },
      description: { type: 'string', default: '', description: 'Supporting text' }
    }
  },
  Footer: {
    type: 'Footer',
    label: 'Footer',
    comment: 'Page footer area.',
    keywords: ['footer', 'layout', 'navigation'],
    category: 'Organism',
    propSchema: {
      text: { type: 'string', default: 'Footer text', description: 'Footer copy' }
    }
  },
  FormField: {
    type: 'FormField',
    label: 'Form Field',
    comment: 'Label and hint wrapper for inputs.',
    keywords: ['form', 'field', 'label'],
    category: 'Molecule',
    propSchema: {
      label: { type: 'string', default: 'Label', description: 'Field label' },
      hint: { type: 'string', default: '', description: 'Helper text' }
    }
  },
  Heading: {
    type: 'Heading',
    label: 'Heading',
    comment: 'Section heading.',
    keywords: ['heading', 'title', 'text'],
    category: 'Atom',
    propSchema: {
      text: { type: 'string', default: 'Heading', description: 'Heading text' },
      level: { type: 'number', default: 2, description: 'Heading level' }
    }
  },
  HeroSection: {
    type: 'HeroSection',
    label: 'Hero Section',
    comment: 'Hero banner with title and subtitle.',
    keywords: ['hero', 'banner', 'header'],
    category: 'Organism',
    propSchema: {
      title: { type: 'string', default: 'Hero title', description: 'Title text' },
      subtitle: { type: 'string', default: 'Subtitle', description: 'Subtitle text' }
    }
  },
  Icon: {
    type: 'Icon',
    label: 'Icon',
    comment: 'Icon glyph display.',
    keywords: ['icon', 'glyph'],
    category: 'Atom',
    propSchema: {
      name: { type: 'string', default: '★', description: 'Icon glyph' }
    }
  },
  IconButton: {
    type: 'IconButton',
    label: 'Icon Button',
    comment: 'Button with icon.',
    keywords: ['icon', 'button', 'action'],
    category: 'Atom',
    propSchema: {
      icon: { type: 'string', default: '★', description: 'Icon glyph' },
      label: { type: 'string', default: '', description: 'Accessible label' },
      variant: { type: 'string', default: 'ghost', enum: ['primary', 'secondary', 'ghost'], description: 'Variant' },
      size: { type: 'string', default: 'md', enum: ['sm', 'md', 'lg'], description: 'Size' }
    }
  },
  Image: {
    type: 'Image',
    label: 'Image',
    comment: 'Responsive image.',
    keywords: ['image', 'media', 'photo'],
    category: 'Atom',
    propSchema: {
      src: { type: 'string', default: '', description: 'Image URL' },
      alt: { type: 'string', default: '', description: 'Alt text' },
      width: { type: 'string', default: '100%', description: 'Width' }
    }
  },
  Input: {
    type: 'Input',
    label: 'Input',
    comment: 'Labeled text input.',
    keywords: ['input', 'text', 'field'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: '', description: 'Field label' },
      type: { type: 'string', default: 'text', description: 'Input type' },
      placeholder: { type: 'string', default: '', description: 'Placeholder' },
      id: { type: 'string', default: '', description: 'Input id' }
    }
  },
  InputGroup: {
    type: 'InputGroup',
    label: 'Input Group',
    comment: 'Grouped inputs with label.',
    keywords: ['input', 'group', 'form'],
    category: 'Molecule',
    propSchema: {
      label: { type: 'string', default: '', description: 'Group label' }
    }
  },
  Label: {
    type: 'Label',
    label: 'Label',
    comment: 'Text label element.',
    keywords: ['label', 'text'],
    category: 'Atom',
    propSchema: {
      text: { type: 'string', default: 'Label', description: 'Label text' }
    }
  },
  Link: {
    type: 'Link',
    label: 'Link',
    comment: 'Inline link.',
    keywords: ['link', 'anchor', 'navigation'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: 'Link', description: 'Link label' },
      href: { type: 'string', default: '#', description: 'Target URL' }
    }
  },
  List: {
    type: 'List',
    label: 'List',
    comment: 'Simple list of items.',
    keywords: ['list', 'items'],
    category: 'Molecule',
    propSchema: {
      items: { type: 'string[]', default: ['Item 1', 'Item 2'], description: 'Items list' }
    }
  },
  Modal: {
    type: 'Modal',
    label: 'Modal',
    comment: 'Overlay dialog container.',
    keywords: ['modal', 'dialog', 'overlay'],
    category: 'Organism',
    propSchema: {
      title: { type: 'string', default: 'Modal title', description: 'Dialog title' },
      open: { type: 'boolean', default: true, description: 'Open state' }
    }
  },
  Pagination: {
    type: 'Pagination',
    label: 'Pagination',
    comment: 'Page navigation controls.',
    keywords: ['pagination', 'pages', 'navigation'],
    category: 'Molecule',
    propSchema: {
      page: { type: 'number', default: 1, description: 'Current page' },
      total: { type: 'number', default: 10, description: 'Total pages' }
    }
  },
  PasswordField: {
    type: 'PasswordField',
    label: 'Password Field',
    comment: 'Password input with label and placeholder.',
    keywords: ['password', 'input', 'field'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: 'Password', description: 'Field label' },
      placeholder: { type: 'string', default: 'Enter password', description: 'Placeholder' }
    }
  },
  ProgressBar: {
    type: 'ProgressBar',
    label: 'Progress Bar',
    comment: 'Progress indicator.',
    keywords: ['progress', 'loading', 'status'],
    category: 'Atom',
    propSchema: {
      value: { type: 'number', default: 0, description: 'Progress value' }
    }
  },
  Radio: {
    type: 'Radio',
    label: 'Radio',
    comment: 'Single radio option.',
    keywords: ['radio', 'input', 'option'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: 'Option', description: 'Label text' },
      value: { type: 'string', default: 'option', description: 'Option value' },
      group: { type: 'string', default: 'group', description: 'Group name' }
    }
  },
  RadioGroup: {
    type: 'RadioGroup',
    label: 'Radio Group',
    comment: 'Group of radio options.',
    keywords: ['radio', 'group', 'options'],
    category: 'Molecule',
    propSchema: {
      options: { type: 'string[]', default: ['Option A', 'Option B'], description: 'Options list' },
      group: { type: 'string', default: 'group', description: 'Group name' }
    }
  },
  SearchBar: {
    type: 'SearchBar',
    label: 'Search Bar',
    comment: 'Search input with button.',
    keywords: ['search', 'input', 'toolbar'],
    category: 'Molecule',
    hasPart: ['SearchField', 'Button'],
    propSchema: {
      placeholder: { type: 'string', default: 'Search', description: 'Placeholder' },
      value: { type: 'string', default: '', description: 'Search value' }
    }
  },
  SearchField: {
    type: 'SearchField',
    label: 'Search Field',
    comment: 'Minimal search input.',
    keywords: ['search', 'input', 'field'],
    category: 'Atom',
    propSchema: {
      placeholder: { type: 'string', default: 'Search', description: 'Placeholder' }
    }
  },
  Select: {
    type: 'Select',
    label: 'Select',
    comment: 'Dropdown selection input.',
    keywords: ['select', 'dropdown', 'input'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: '', description: 'Field label' },
      options: { type: 'string[]', default: ['Option A', 'Option B'], description: 'Options list' },
      value: { type: 'string', default: '', description: 'Selected value' }
    }
  },
  SelectField: {
    type: 'SelectField',
    label: 'Select Field',
    comment: 'Labeled dropdown field.',
    keywords: ['select', 'dropdown', 'field'],
    category: 'Molecule',
    propSchema: {
      label: { type: 'string', default: '', description: 'Field label' },
      options: { type: 'string[]', default: ['Option A', 'Option B'], description: 'Options list' }
    }
  },
  SideNav: {
    type: 'SideNav',
    label: 'Side Nav',
    comment: 'Vertical navigation menu.',
    keywords: ['navigation', 'sidebar', 'menu'],
    category: 'Organism',
    propSchema: {
      items: { type: 'string[]', default: ['Home', 'Settings'], description: 'Nav items' }
    }
  },
  Slider: {
    type: 'Slider',
    label: 'Slider',
    comment: 'Range slider input.',
    keywords: ['slider', 'range', 'input'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: '', description: 'Field label' },
      value: { type: 'number', default: 0, description: 'Current value' },
      min: { type: 'number', default: 0, description: 'Minimum value' },
      max: { type: 'number', default: 100, description: 'Maximum value' }
    }
  },
  Spinner: {
    type: 'Spinner',
    label: 'Spinner',
    comment: 'Loading spinner.',
    keywords: ['spinner', 'loading', 'progress'],
    category: 'Atom',
    propSchema: {
      size: { type: 'number', default: 24, description: 'Spinner size' }
    }
  },
  StatCard: {
    type: 'StatCard',
    label: 'Stat Card',
    comment: 'Statistic highlight card.',
    keywords: ['stats', 'card', 'metric'],
    category: 'Molecule',
    propSchema: {
      label: { type: 'string', default: 'Metric', description: 'Label text' },
      value: { type: 'string', default: '0', description: 'Value text' }
    }
  },
  StatusDot: {
    type: 'StatusDot',
    label: 'Status Dot',
    comment: 'Presence indicator dot.',
    keywords: ['status', 'presence', 'indicator'],
    category: 'Atom',
    propSchema: {
      status: { type: 'string', default: 'online', enum: ['online', 'offline', 'busy'], description: 'Status value' }
    }
  },
  Table: {
    type: 'Table',
    label: 'Table',
    comment: 'Data table.',
    keywords: ['table', 'data', 'grid'],
    category: 'Organism',
    propSchema: {
      columns: { type: 'string[]', default: ['Name', 'Value'], description: 'Column headers' },
      rows: { type: 'array', default: [{ Name: 'Item', Value: 'Value' }], description: 'Row data' }
    }
  },
  Tabs: {
    type: 'Tabs',
    label: 'Tabs',
    comment: 'Tabbed content navigation.',
    keywords: ['tabs', 'navigation', 'switch'],
    category: 'Molecule',
    propSchema: {
      tabs: { type: 'string[]', default: ['Tab 1', 'Tab 2'], description: 'Tab labels' },
      active: { type: 'string', default: 'Tab 1', description: 'Active tab' }
    }
  },
  Tag: {
    type: 'Tag',
    label: 'Tag',
    comment: 'Tag label.',
    keywords: ['tag', 'label', 'category'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: 'Tag', description: 'Tag text' }
    }
  },
  Text: {
    type: 'Text',
    label: 'Text',
    comment: 'Body text block.',
    keywords: ['text', 'copy', 'paragraph'],
    category: 'Atom',
    propSchema: {
      text: { type: 'string', default: '', description: 'Text content' }
    }
  },
  Textarea: {
    type: 'Textarea',
    label: 'Textarea',
    comment: 'Multi-line text input.',
    keywords: ['textarea', 'input', 'multiline'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: '', description: 'Field label' },
      placeholder: { type: 'string', default: '', description: 'Placeholder' },
      rows: { type: 'number', default: 4, description: 'Row count' },
      value: { type: 'string', default: '', description: 'Value' }
    }
  },
  ToggleField: {
    type: 'ToggleField',
    label: 'Toggle Field',
    comment: 'Labeled toggle field.',
    keywords: ['toggle', 'switch', 'field'],
    category: 'Molecule',
    propSchema: {
      label: { type: 'string', default: '', description: 'Field label' },
      checked: { type: 'boolean', default: false, description: 'Checked state' }
    }
  },
  ToggleSwitch: {
    type: 'ToggleSwitch',
    label: 'Toggle Switch',
    comment: 'Toggle switch control.',
    keywords: ['toggle', 'switch', 'input'],
    category: 'Atom',
    propSchema: {
      label: { type: 'string', default: '', description: 'Label text' },
      checked: { type: 'boolean', default: false, description: 'Checked state' }
    }
  },
  Toolbar: {
    type: 'Toolbar',
    label: 'Toolbar',
    comment: 'Horizontal toolbar area.',
    keywords: ['toolbar', 'actions', 'header'],
    category: 'Organism',
    propSchema: {
      title: { type: 'string', default: 'Toolbar', description: 'Toolbar title' }
    }
  },
  Tooltip: {
    type: 'Tooltip',
    label: 'Tooltip',
    comment: 'Hover tooltip text.',
    keywords: ['tooltip', 'hint', 'help'],
    category: 'Atom',
    propSchema: {
      text: { type: 'string', default: 'Tooltip', description: 'Tooltip text' }
    }
  },
  TopNav: {
    type: 'TopNav',
    label: 'Top Nav',
    comment: 'Top navigation bar.',
    keywords: ['navigation', 'topbar', 'menu'],
    category: 'Organism',
    propSchema: {
      title: { type: 'string', default: 'Top Nav', description: 'Navigation title' }
    }
  }
};
