import Container from './components/Container.svelte';
import Input from './components/Input.svelte';
import Button from './components/Button.svelte';

export const designSystem: Record<string, any> = {
  'LoginCard': Container,
  'TodoList': Container,
  'KanbanBoard': Container,
  'Molecule': Container,
  
  'EmailInput': Input,
  'PasswordInput': Input,
  'SearchInput': Input,
  'TodoInput': Input,
  'SubmitButton': Button,
  'SearchIcon': Button,
  
  'default': Container
};