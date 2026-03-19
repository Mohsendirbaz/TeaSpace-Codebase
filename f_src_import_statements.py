import os
import re
import json
import pandas as pd
import networkx as nx
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import matplotlib.pyplot as plt

@dataclass
class AnalysisConfig:
    """Configuration settings for enhanced React project analysis"""
    src_dir: str
    output_dir: str
    version_control_file: str = "version_control.json"
    
    # Analysis depth settings
    max_line_analysis: int = 500  # Increased from 52 to 500
    scan_full_file: bool = True
    
    # Analysis scope settings
    analyze_relative_paths: bool = True
    analyze_css_imports: bool = True
    analyze_component_imports: bool = True
    analyze_hooks_usage: bool = True
    analyze_state_management: bool = True
    analyze_context_usage: bool = True
    
    # File filtering settings
    exclude_dirs: List[str] = field(default_factory=lambda: ['node_modules', 'build', 'dist', '.git'])
    include_extensions: List[str] = field(default_factory=lambda: ['.js', '.jsx', '.ts', '.tsx', '.scss', '.css', '.less'])
    
    # Code pattern recognition
    detect_custom_hooks: bool = True
    detect_context_providers: bool = True
    detect_state_hooks: bool = True
    
    # Report generation settings
    generate_component_map: bool = True
    generate_style_map: bool = True
    generate_dependency_graph: bool = True
    generate_optimization_report: bool = True
    generate_state_flow_diagram: bool = True
    
    @staticmethod
    def create_default():
        """Create a default configuration instance"""
        base_path = Path.cwd()
        return AnalysisConfig(
            src_dir=str(base_path / "src"),
            output_dir=str(base_path / "src_analysis_results")
        )

@dataclass
class ImportInfo:
    """Information about an import statement"""
    source: str
    import_type: str  # 'default', 'named', 'namespace', 'css', 'dynamic'
    imported_names: List[str] = field(default_factory=list)
    is_relative: bool = False
    resolved_path: str = ""

@dataclass
class HookUsage:
    """Information about React hook usage"""
    hook_name: str
    state_variable: Optional[str] = None
    setter_function: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

@dataclass
class ComponentInfo:
    """Enhanced information about a React component"""
    name: str
    type: str  # 'functional', 'class', 'hook', 'context', 'unknown'
    imports: List[ImportInfo] = field(default_factory=list)
    hooks: List[HookUsage] = field(default_factory=list)
    props: List[str] = field(default_factory=list)
    state: List[str] = field(default_factory=list)
    css_modules: List[str] = field(default_factory=list)
    contexts_used: List[str] = field(default_factory=list)
    renders_components: List[str] = field(default_factory=list)

@dataclass
class FileAnalysis:
    """Enhanced structure for storing file analysis results"""
    file_path: str
    component_name: str
    content: str
    imports: List[ImportInfo] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    components: List[ComponentInfo] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    style_dependencies: List[str] = field(default_factory=list)

class EnhancedProjectAnalyzer:
    """Enhanced analyzer for React project structure and relationships"""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.root_dir = Path(config.src_dir)
        self.output_dir = Path(config.output_dir)
        self.analysis_results: Dict[str, FileAnalysis] = {}
        self.component_map: Dict[str, ComponentInfo] = {}
        self.dependency_graph = nx.DiGraph()
        self.style_dependency_graph = nx.DiGraph()
        self.state_flow_graph = nx.DiGraph()
        self.project_structure: Dict = {}
        self.version_control_path = self.output_dir / config.version_control_file
        os.makedirs(self.output_dir, exist_ok=True)

    def analyze_project(self) -> None:
        """Execute the enhanced project analysis process with version control."""
        print(f"Starting analysis of {self.root_dir}...")
        
        # Load previous version control data if it exists
        previous_analysis = self._load_previous_analysis()
        
        # Perform current analysis
        self._scan_directory()
        self._analyze_files()
        self._build_dependency_graphs()
        
        # Generate or update reports
        self._generate_project_structure(previous_analysis)
        
        if self.config.generate_component_map:
            self._generate_component_map()
        if self.config.generate_style_map:
            self._generate_style_map()
        if self.config.generate_dependency_graph:
            self._generate_dependency_graph()
        if self.config.generate_optimization_report:
            self._generate_optimization_report()
        if self.config.generate_state_flow_diagram:
            self._generate_state_flow_diagram()
            
        print(f"Analysis complete. Results saved to {self.output_dir}")

    def _load_previous_analysis(self) -> Optional[Dict]:
        """Load previous analysis data from version control file."""
        try:
            if self.version_control_path.exists():
                with open(self.version_control_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading previous analysis: {str(e)}")
        return None

    def _extract_component_name(self, file_path: Path, content: str) -> str:
        """Extract the primary component name from a file based on content analysis."""
        # Start with filename-based guess
        component_name = file_path.stem
        
        # Convert non-pascal case to pascal case if it's not already
        if not (component_name[0].isupper() and any(c.islower() for c in component_name)):
            words = re.findall(r'[A-Za-z][a-z]*', component_name)
            component_name = ''.join(word.capitalize() for word in words)
        
        # Look for component declarations in the content
        component_patterns = [
            # Function component patterns
            r'function\s+([A-Z][A-Za-z0-9_]*)\s*\(',
            r'const\s+([A-Z][A-Za-z0-9_]*)\s*=\s*\(\s*(?:{[^}]*}|[^)]*)\s*\)\s*=>\s*{',
            r'const\s+([A-Z][A-Za-z0-9_]*)\s*=\s*\(\s*(?:{[^}]*}|[^)]*)\s*\)\s*=>\s*\(',
            r'const\s+([A-Z][A-Za-z0-9_]*)\s*=\s*React\.(?:memo|forwardRef)',
            # Class component patterns
            r'class\s+([A-Z][A-Za-z0-9_]*)\s+extends\s+(?:React\.)?Component',
            r'class\s+([A-Z][A-Za-z0-9_]*)\s+extends\s+(?:React\.)?PureComponent',
            # Context component patterns
            r'const\s+([A-Z][A-Za-z0-9_]*Context)\s*=\s*(?:React\.)?createContext',
            # Hook patterns
            r'function\s+(use[A-Z][A-Za-z0-9_]*)\s*\(',
            r'const\s+(use[A-Z][A-Za-z0-9_]*)\s*=\s*\(\s*(?:{[^}]*}|[^)]*)\s*\)\s*=>\s*{',
        ]
        
        for pattern in component_patterns:
            matches = re.search(pattern, content)
            if matches:
                return matches.group(1)
        
        # If no declaration found, check for export default statements
        export_default_patterns = [
            r'export\s+default\s+([A-Z][A-Za-z0-9_]*)',
            r'export\s+{\s*([A-Z][A-Za-z0-9_]*)\s+as\s+default\s*}'
        ]
        
        for pattern in export_default_patterns:
            matches = re.search(pattern, content)
            if matches:
                return matches.group(1)
        
        return component_name

    def _extract_exports(self, content: str) -> List[str]:
        """Extract exported entities from the file content."""
        exports = []
        
        # Named exports
        named_exports_pattern = r'export\s+(?:const|let|var|function|class)\s+([A-Za-z0-9_]+)'
        exports.extend(re.findall(named_exports_pattern, content))
        
        # Export statements
        export_statement_pattern = r'export\s+{\s*([^}]+)\s*}'
        for match in re.findall(export_statement_pattern, content):
            names = [name.strip().split(' as ')[0].strip() for name in match.split(',')]
            exports.extend(names)
        
        # Default export
        default_export_pattern = r'export\s+default\s+([A-Za-z0-9_]+)'
        default_matches = re.findall(default_export_pattern, content)
        if default_matches:
            exports.append(f"{default_matches[0]} (default)")
        
        return exports

    def _extract_imports(self, content: str, file_path: Path) -> List[ImportInfo]:
        """Extract detailed import information from file content."""
        imports = []
        
        # ES6 import patterns
        es6_import_patterns = [
            # Import default
            (r'import\s+([A-Za-z0-9_]+)\s+from\s+[\'"]([^\'"]+)[\'"]', 'default'),
            # Import named
            (r'import\s+{\s*([^}]+)\s*}\s+from\s+[\'"]([^\'"]+)[\'"]', 'named'),
            # Import default and named
            (r'import\s+([A-Za-z0-9_]+)\s*,\s*{\s*([^}]+)\s*}\s+from\s+[\'"]([^\'"]+)[\'"]', 'mixed'),
            # Import namespace
            (r'import\s+\*\s+as\s+([A-Za-z0-9_]+)\s+from\s+[\'"]([^\'"]+)[\'"]', 'namespace'),
            # Import CSS/resource
            (r'import\s+[\'"]([^\'"]+\.(css|scss|less|svg|png|jpg|jpeg|gif))[\'"]', 'css'),
            # Dynamic import
            (r'import\(\s*[\'"]([^\'"]+)[\'"]\s*\)', 'dynamic')
        ]
        
        for pattern, import_type in es6_import_patterns:
            for match in re.finditer(pattern, content):
                if import_type == 'default':
                    name, source = match.groups()
                    imports.append(ImportInfo(
                        source=source,
                        import_type=import_type,
                        imported_names=[name],
                        is_relative=source.startswith('.')
                    ))
                elif import_type == 'named':
                    names_str, source = match.groups()
                    names = [n.strip().split(' as ')[0].strip() for n in names_str.split(',')]
                    imports.append(ImportInfo(
                        source=source,
                        import_type=import_type,
                        imported_names=names,
                        is_relative=source.startswith('.')
                    ))
                elif import_type == 'mixed':
                    default_name, named_str, source = match.groups()
                    names = [n.strip().split(' as ')[0].strip() for n in named_str.split(',')]
                    imports.append(ImportInfo(
                        source=source,
                        import_type=import_type,
                        imported_names=[default_name] + names,
                        is_relative=source.startswith('.')
                    ))
                elif import_type == 'namespace':
                    name, source = match.groups()
                    imports.append(ImportInfo(
                        source=source,
                        import_type=import_type,
                        imported_names=[name],
                        is_relative=source.startswith('.')
                    ))
                elif import_type == 'css':
                    source = match.group(1)
                    imports.append(ImportInfo(
                        source=source,
                        import_type='css',
                        is_relative=source.startswith('.')
                    ))
                elif import_type == 'dynamic':
                    source = match.group(1)
                    imports.append(ImportInfo(
                        source=source,
                        import_type='dynamic',
                        is_relative=source.startswith('.')
                    ))

        # CommonJS require patterns
        require_pattern = r'(?:const|let|var)\s+([A-Za-z0-9_{}]+)\s*=\s*require\([\'"]([^\'"]+)[\'"]\)'
        for match in re.finditer(require_pattern, content):
            var_name, source = match.groups()
            # Handle destructuring
            if var_name.startswith('{') and var_name.endswith('}'):
                names_str = var_name[1:-1]
                names = [n.strip().split(':')[0].strip() for n in names_str.split(',')]
                imports.append(ImportInfo(
                    source=source,
                    import_type='named',
                    imported_names=names,
                    is_relative=source.startswith('.')
                ))
            else:
                imports.append(ImportInfo(
                    source=source,
                    import_type='default',
                    imported_names=[var_name],
                    is_relative=source.startswith('.')
                ))
        
        # Resolve relative paths
        for imp in imports:
            if imp.is_relative:
                imp.resolved_path = self._resolve_import_path(file_path, imp.source)
        
        return imports

    def _resolve_import_path(self, file_path: Path, import_path: str) -> str:
        """Resolve a relative import path to an absolute project path."""
        if not import_path.startswith('.'):
            return import_path  # External package
        
        base_dir = file_path.parent
        
        # Handle file extension if not provided
        if not import_path.endswith(tuple(self.config.include_extensions)):
            # Try to add various extensions to find the file
            for ext in ['.js', '.jsx', '.ts', '.tsx']:
                potential_path = f"{import_path}{ext}"
                if (base_dir / potential_path).resolve().exists():
                    import_path = potential_path
                    break
                
                # Check for index files
                if import_path.endswith('/') or not '.' in Path(import_path).name:
                    potential_index = f"{import_path}/index{ext}"
                    if (base_dir / potential_index).resolve().exists():
                        import_path = potential_index
                        break
        
        try:
            resolved = (base_dir / import_path).resolve()
            if resolved.exists():
                # Get path relative to the project root
                return str(resolved.relative_to(self.root_dir))
            else:
                # If the file doesn't exist, make a best guess
                return str((base_dir / import_path))
        except Exception as e:
            print(f"Error resolving path {import_path} from {file_path}: {str(e)}")
            return import_path

    def _extract_hook_usage(self, content: str) -> List[HookUsage]:
        """Extract React hook usage information from file content."""
        hooks = []
        
        # useState pattern
        use_state_pattern = r'const\s+\[([A-Za-z0-9_]+),\s*set([A-Za-z0-9_]+)\]\s*=\s*(?:React\.)?useState\(([^)]*)\)'
        for match in re.finditer(use_state_pattern, content):
            state_var, setter_suffix, initial = match.groups()
            setter = f"set{setter_suffix}"
            hooks.append(HookUsage(
                hook_name="useState",
                state_variable=state_var,
                setter_function=setter
            ))
        
        # useEffect pattern
        use_effect_pattern = r'(?:React\.)?useEffect\(\s*\(\)\s*=>\s*{[^}]*},\s*\[([^]]*)\]\s*\)'
        for match in re.finditer(use_effect_pattern, content):
            deps_str = match.group(1)
            deps = [d.strip() for d in deps_str.split(',')] if deps_str.strip() else []
            hooks.append(HookUsage(
                hook_name="useEffect",
                dependencies=deps
            ))
        
        # useCallback pattern
        use_callback_pattern = r'const\s+([A-Za-z0-9_]+)\s*=\s*(?:React\.)?useCallback\([^,]+,\s*\[([^]]*)\]\s*\)'
        for match in re.finditer(use_callback_pattern, content):
            func_name, deps_str = match.groups()
            deps = [d.strip() for d in deps_str.split(',')] if deps_str.strip() else []
            hooks.append(HookUsage(
                hook_name="useCallback",
                state_variable=func_name,
                dependencies=deps
            ))
        
        # useMemo pattern
        use_memo_pattern = r'const\s+([A-Za-z0-9_]+)\s*=\s*(?:React\.)?useMemo\([^,]+,\s*\[([^]]*)\]\s*\)'
        for match in re.finditer(use_memo_pattern, content):
            memo_name, deps_str = match.groups()
            deps = [d.strip() for d in deps_str.split(',')] if deps_str.strip() else []
            hooks.append(HookUsage(
                hook_name="useMemo",
                state_variable=memo_name,
                dependencies=deps
            ))
        
        # useRef pattern
        use_ref_pattern = r'const\s+([A-Za-z0-9_]+)\s*=\s*(?:React\.)?useRef\('
        for match in re.finditer(use_ref_pattern, content):
            ref_name = match.group(1)
            hooks.append(HookUsage(
                hook_name="useRef",
                state_variable=ref_name
            ))
        
        # useContext pattern
        use_context_pattern = r'const\s+([A-Za-z0-9_]+)\s*=\s*(?:React\.)?useContext\(([A-Za-z0-9_]+)\)'
        for match in re.finditer(use_context_pattern, content):
            context_var, context_name = match.groups()
            hooks.append(HookUsage(
                hook_name="useContext",
                state_variable=context_var,
                dependencies=[context_name]
            ))
        
        # Custom hooks
        custom_hook_pattern = r'const\s+([A-Za-z0-9_]+)\s*=\s*(use[A-Z][A-Za-z0-9_]*)\('
        for match in re.finditer(custom_hook_pattern, content):
            hook_var, hook_name = match.groups()
            if not hook_name.startswith('useState') and not hook_name.startswith('useEffect'):
                hooks.append(HookUsage(
                    hook_name=hook_name,
                    state_variable=hook_var
                ))
        
        return hooks

    def _extract_component_info(self, file_path: Path, content: str, component_name: str) -> ComponentInfo:
        """Extract detailed component information from file content."""
        # Determine component type
        component_type = 'unknown'
        if re.search(r'class\s+[A-Za-z0-9_]+\s+extends\s+(?:React\.)?(?:Pure)?Component', content):
            component_type = 'class'
        elif re.search(r'function\s+[A-Za-z0-9_]+|const\s+[A-Za-z0-9_]+\s*=\s*\(', content):
            if component_name.startswith('use'):
                component_type = 'hook'
            elif 'Context' in component_name and re.search(r'createContext', content):
                component_type = 'context'
            else:
                component_type = 'functional'
        
        # Extract props for functional components
        props = []
        if component_type == 'functional':
            props_patterns = [
                r'function\s+[A-Za-z0-9_]+\s*\(\s*{\s*([^}]*)\s*}\s*\)',
                r'const\s+[A-Za-z0-9_]+\s*=\s*\(\s*{\s*([^}]*)\s*}\s*\)\s*=>',
                r'const\s+[A-Za-z0-9_]+\s*=\s*\(\s*props\s*\)'
            ]
            for pattern in props_patterns:
                match = re.search(pattern, content)
                if match and "{" in pattern:
                    props_str = match.group(1)
                    props = [p.strip().split(':')[0].strip() for p in props_str.split(',') if p.strip()]
                elif match:
                    props = ['props (object)']
        
        # Extract state for class components
        state = []
        if component_type == 'class':
            state_pattern = r'this\.state\s*=\s*{\s*([^}]*)\s*}'
            match = re.search(state_pattern, content)
            if match:
                state_str = match.group(1)
                state = [s.strip().split(':')[0].strip() for s in state_str.split(',') if s.strip()]
        
        # Extract hooks usage for functional components
        hooks = []
        if component_type in ['functional', 'hook']:
            hooks = self._extract_hook_usage(content)
            # Add state from useState hooks
            for hook in hooks:
                if hook.hook_name == 'useState' and hook.state_variable:
                    state.append(hook.state_variable)
        
        # Extract CSS modules
        css_modules = []
        css_import_pattern = r'import\s+([A-Za-z0-9_]+)\s+from\s+[\'"]([^\'"]+(\.module)?\.css)[\'"]'
        for match in re.finditer(css_import_pattern, content):
            module_name, path, _ = match.groups()
            css_modules.append(f"{module_name} ({path})")
        
        # Extract contexts used
        contexts_used = []
        context_pattern = r'(?:React\.)?useContext\(([A-Za-z0-9_]+)\)'
        for match in re.finditer(context_pattern, content):
            contexts_used.append(match.group(1))
        
        # Extract components rendered
        rendered_components = []
        render_pattern = r'<([A-Z][A-Za-z0-9_]*)'
        for match in re.finditer(render_pattern, content):
            component = match.group(1)
            if component not in rendered_components and component != component_name:
                rendered_components.append(component)
        
        return ComponentInfo(
            name=component_name,
            type=component_type,
            props=props,
            state=state,
            hooks=hooks,
            css_modules=css_modules,
            contexts_used=contexts_used,
            renders_components=rendered_components
        )

    def _scan_directory(self) -> None:
        """Scan the project directory for all relevant files, excluding specified directories."""
        print("Scanning project files...")
        
        for file_path in self.root_dir.rglob('*'):
            # Skip excluded directories
            if any(excluded in str(file_path) for excluded in self.config.exclude_dirs):
                continue
                
            # Only process files with specified extensions
            if file_path.is_file() and file_path.suffix in self.config.include_extensions:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    rel_path = file_path.relative_to(self.root_dir)
                    rel_path_str = str(rel_path).replace('\\', '/')  # Normalize path separators
                    
                    # Extract component name
                    component_name = self._extract_component_name(file_path, content)
                    
                    # Extract imports
                    imports = self._extract_imports(content, file_path)
                    
                    # Extract exports
                    exports = self._extract_exports(content)
                    
                    # Store file info in project structure
                    self.project_structure[rel_path_str] = {
                        'type': file_path.suffix,
                        'directory': str(rel_path.parent).replace('\\', '/'),
                        'name': file_path.name,
                        'component_name': component_name,
                        'imports': [imp.source for imp in imports],
                        'exports': exports,
                        'content': content if self.config.scan_full_file else content[:self.config.max_line_analysis]
                    }
                    
                except Exception as e:
                    print(f"Error reading file {file_path}: {str(e)}")
        
        print(f"Scanned {len(self.project_structure)} files")

    def _analyze_files(self) -> None:
        """Analyze all files for components, imports, and relationships."""
        print("Analyzing files for components and relationships...")
        
        for file_path, info in self.project_structure.items():
            content = info['content']
            component_name = info['component_name']
            
            # Extract component information
            component_info = self._extract_component_info(Path(file_path), content, component_name)
            
            # Extract imports
            imports = self._extract_imports(content, Path(file_path))
            
            # Process dependencies
            dependencies = []
            style_dependencies = []
            for imp in imports:
                if imp.is_relative and imp.resolved_path:
                    if imp.source.endswith(('.css', '.scss', '.less')):
                        style_dependencies.append(imp.resolved_path)
                    else:
                        dependencies.append(imp.resolved_path)
            
            # Create file analysis object
            self.analysis_results[file_path] = FileAnalysis(
                file_path=file_path,
                component_name=component_name,
                content=content,
                imports=imports,
                exports=info['exports'],
                components=[component_info],
                dependencies=dependencies,
                style_dependencies=style_dependencies
            )
            
            # Add to component map
            if component_info.name:
                self.component_map[component_info.name] = component_info

    def _build_dependency_graphs(self) -> None:
        """Build dependency graphs for components, styles, and state flow."""
        print("Building dependency graphs...")
        
        # Component dependency graph
        for file_path, analysis in self.analysis_results.items():
            self.dependency_graph.add_node(file_path, label=analysis.component_name)
            for dep in analysis.dependencies:
                if dep in self.analysis_results:
                    self.dependency_graph.add_edge(file_path, dep)
            
            # Style dependency graph
            for style_dep in analysis.style_dependencies:
                self.style_dependency_graph.add_edge(file_path, style_dep)
        
        # State flow graph - tracking how state is passed between components
        for file_path, analysis in self.analysis_results.items():
            component_name = analysis.component_name
            
            for component in analysis.components:
                # Add node for this component
                self.state_flow_graph.add_node(component_name)
                
                # Check components it renders and add edges for potential prop drilling
                for rendered in component.renders_components:
                    if rendered in self.component_map:
                        self.state_flow_graph.add_edge(component_name, rendered, type='props')
                
                # Check contexts it might provide
                if component.type == 'context':
                    for file_dep, dep_analysis in self.analysis_results.items():
                        for dep_component in dep_analysis.components:
                            if component_name in dep_component.contexts_used:
                                self.state_flow_graph.add_edge(component_name, dep_component.name, type='context')

    def _generate_project_structure(self, previous_analysis: Optional[Dict]) -> None:
        """Generate project structure report with version control."""
        print("Generating project structure report...")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        structure = {
            'project_name': self.root_dir.name,
            'analysis_date': timestamp,
            'version': 1,
            'directories': {},
            'files': {}
        }
        
        # Build current structure
        for file_path, info in self.project_structure.items():
            structure['files'][file_path] = {
                'type': info['type'],
                'directory': info['directory'],
                'imports': info['imports'],
                'exports': info['exports']
            }
            
            dir_path = info['directory']
            if dir_path not in structure['directories']:
                structure['directories'][dir_path] = {
                    'files': [],
                    'import_count': 0
                }
            structure['directories'][dir_path]['files'].append(file_path)
            structure['directories'][dir_path]['import_count'] += len(info['imports'])
        
        # Handle version control
        if previous_analysis:
            structure['version'] = previous_analysis.get('version', 0) + 1
            changes = self._compare_analyses(previous_analysis, structure)
            structure['changes'] = changes
            
            # Write detailed change log
            change_log_path = self.output_dir / f'change_log_{datetime.now().strftime("%Y%m%d_%H%M")}.md'
            self._write_change_log(changes, change_log_path)
        
        # Always update the main version control file
        with open(self.version_control_path, 'w', encoding='utf-8') as f:
            json.dump(structure, f, indent=2)

    def _compare_analyses(self, previous: Dict, current: Dict) -> Dict:
        """Compare previous and current analyses to identify changes."""
        previous_files = set(previous.get('files', {}).keys())
        current_files = set(current.get('files', {}).keys())
        
        changes = {
            'added_files': list(current_files - previous_files),
            'removed_files': list(previous_files - current_files),
            'modified_files': [],
            'import_changes': [],
            'component_changes': [],
            'directory_changes': []
        }
        
        # Check for modified files
        common_files = previous_files & current_files
        for file in common_files:
            prev_imports = set(previous['files'][file].get('imports', []))
            curr_imports = set(current['files'][file].get('imports', []))
            
            if prev_imports != curr_imports:
                changes['modified_files'].append(file)
                changes['import_changes'].append({
                    'file': file,
                    'added_imports': list(curr_imports - prev_imports),
                    'removed_imports': list(prev_imports - curr_imports)
                })
                
        # Check for directory structure changes
        prev_dirs = set(previous.get('directories', {}).keys())
        curr_dirs = set(current.get('directories', {}).keys())
        
        changes['directory_changes'] = {
            'added': list(curr_dirs - prev_dirs),
            'removed': list(prev_dirs - curr_dirs)
        }
        
        return changes

    def _write_change_log(self, changes: Dict, log_path: Path) -> None:
        """Write a detailed change log in Markdown format."""
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"# Project Structure Changes\n\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if changes['added_files']:
                f.write("## Added Files\n\n")
                for file in changes['added_files']:
                    f.write(f"- {file}\n")
                f.write("\n")
            
            if changes['removed_files']:
                f.write("## Removed Files\n\n")
                for file in changes['removed_files']:
                    f.write(f"- {file}\n")
                f.write("\n")
            
            if changes['modified_files']:
                f.write("## Modified Files\n\n")
                for file in changes['modified_files']:
                    f.write(f"- {file}\n")
                f.write("\n")
            
            if changes['import_changes']:
                f.write("## Import Changes\n\n")
                for change in changes['import_changes']:
                    f.write(f"### {change['file']}\n\n")
                    
                    if change['added_imports']:
                        f.write("Added imports:\n")
                        for imp in change['added_imports']:
                            f.write(f"- `{imp}`\n")
                        f.write("\n")
                    
                    if change['removed_imports']:
                        f.write("Removed imports:\n")
                        for imp in change['removed_imports']:
                            f.write(f"- `{imp}`\n")
                        f.write("\n")
            
            if changes['directory_changes']['added'] or changes['directory_changes']['removed']:
                f.write("## Directory Structure Changes\n\n")
                
                if changes['directory_changes']['added']:
                    f.write("### Added Directories\n\n")
                    for dir_path in changes['directory_changes']['added']:
                        f.write(f"- {dir_path}\n")
                    f.write("\n")
                
                if changes['directory_changes']['removed']:
                    f.write("### Removed Directories\n\n")
                    for dir_path in changes['directory_changes']['removed']:
                        f.write(f"- {dir_path}\n")
                    f.write("\n")

    def _generate_component_map(self) -> None:
        """Generate component relationship map with detailed information."""
        print("Generating component relationship map...")
        
        # Create detailed CSV report
        components_data = []
        for component_name, info in self.component_map.items():
            components_data.append({
                'Component': component_name,
                'Type': info.type,
                'Props': ', '.join(info.props),
                'State': ', '.join(info.state),
                'Hooks': ', '.join(h.hook_name for h in info.hooks),
                'Context Usage': ', '.join(info.contexts_used),
                'Renders': ', '.join(info.renders_components)
            })
        
        # Generate relationships data
        relationships_data = []
        for file_path, analysis in self.analysis_results.items():
            for dep in analysis.dependencies:
                if dep in self.analysis_results:
                    relationships_data.append({
                        'Source': analysis.component_name,
                        'Target': self.analysis_results[dep].component_name,
                        'Relationship': 'Imports',
                        'Source File': file_path,
                        'Target File': dep
                    })
            
            for component in analysis.components:
                for rendered in component.renders_components:
                    if rendered in self.component_map:
                        relationships_data.append({
                            'Source': component.name,
                            'Target': rendered,
                            'Relationship': 'Renders',
                            'Source File': file_path,
                            'Target File': 'Unknown'
                        })
        
        # Write to CSV files
        components_df = pd.DataFrame(components_data)
        components_df.to_csv(self.output_dir / 'component_info.csv', index=False)
        
        relationships_df = pd.DataFrame(relationships_data)
        relationships_df.to_csv(self.output_dir / 'component_relationships.csv', index=False)
        
        # Generate visual graph if matplotlib is available
        try:
            self._generate_component_graph()
        except Exception as e:
            print(f"Could not generate component graph visualization: {str(e)}")

    def _generate_component_graph(self) -> None:
        """Generate visual component relationship graph."""
        plt.figure(figsize=(12, 10))
        
        # Create a simplified graph for visualization
        simple_graph = nx.DiGraph()
        
        for file_path, analysis in self.analysis_results.items():
            if analysis.component_name:
                simple_graph.add_node(analysis.component_name)
                for dep in analysis.dependencies:
                    if dep in self.analysis_results and self.analysis_results[dep].component_name:
                        simple_graph.add_edge(analysis.component_name, self.analysis_results[dep].component_name)
        
        # Limit the graph size for readability
        if len(simple_graph) > 30:
            # Keep only the most connected components
            top_nodes = sorted(simple_graph.degree, key=lambda x: x[1], reverse=True)[:30]
            simple_graph = simple_graph.subgraph([n[0] for n in top_nodes])
            
        # Use a spring layout for positioning
        pos = nx.spring_layout(simple_graph, seed=42, k=0.8)
        
        node_colors = []
        for node in simple_graph.nodes():
            if node in self.component_map:
                if self.component_map[node].type == 'functional':
                    node_colors.append('skyblue')
                elif self.component_map[node].type == 'class':
                    node_colors.append('salmon')
                elif self.component_map[node].type == 'hook':
                    node_colors.append('lightgreen')
                elif self.component_map[node].type == 'context':
                    node_colors.append('purple')
                else:
                    node_colors.append('lightgray')
            else:
                node_colors.append('lightgray')
        
        # Draw the graph
        nx.draw(
            simple_graph, 
            pos, 
            with_labels=True, 
            node_color=node_colors,
            node_size=1000, 
            font_size=8,
            arrows=True,
            alpha=0.8,
            edge_color='gray'
        )
        
        # Add a legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='skyblue', markersize=10, label='Functional'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='salmon', markersize=10, label='Class'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgreen', markersize=10, label='Hook'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='purple', markersize=10, label='Context'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgray', markersize=10, label='Unknown')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        plt.title(f'Component Relationship Graph ({len(simple_graph)} components)')
        plt.savefig(self.output_dir / 'component_graph.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _generate_style_map(self) -> None:
        """Generate stylesheet relationship map."""
        print("Generating stylesheet relationship map...")
        
        style_relationships = []
        for file_path, analysis in self.analysis_results.items():
            for imp in analysis.imports:
                if imp.import_type == 'css':
                    style_relationships.append({
                        'Component': analysis.component_name,
                        'Stylesheet': imp.source,
                        'Component File': file_path,
                        'Type': 'CSS Import'
                    })
        
        # Create DataFrame and save to CSV
        if style_relationships:
            df = pd.DataFrame(style_relationships)
            df.to_csv(self.output_dir / 'style_relationships.csv', index=False)
            
            # Generate a graph visualization
            try:
                self._generate_style_graph()
            except Exception as e:
                print(f"Could not generate style graph visualization: {str(e)}")
        else:
            print("No style relationships found.")

    def _generate_style_graph(self) -> None:
        """Generate visual stylesheet relationship graph."""
        # Skip if the graph is empty
        if self.style_dependency_graph.number_of_edges() == 0:
            return
            
        plt.figure(figsize=(12, 10))
        
        # Create a simplified bipartite graph for visualization
        style_graph = nx.Graph()
        
        components = set()
        stylesheets = set()
        
        for file_path, analysis in self.analysis_results.items():
            for imp in analysis.imports:
                if imp.import_type == 'css':
                    component_name = analysis.component_name or file_path
                    stylesheet_name = imp.source
                    
                    # Add nodes and edges
                    components.add(component_name)
                    stylesheets.add(stylesheet_name)
                    style_graph.add_node(component_name, bipartite=0)
                    style_graph.add_node(stylesheet_name, bipartite=1)
                    style_graph.add_edge(component_name, stylesheet_name)
        
        # Limit graph size for readability
        if len(style_graph) > 40:
            # Keep only a subset of nodes
            top_components = sorted([(n, style_graph.degree(n)) for n in components], key=lambda x: x[1], reverse=True)[:20]
            top_stylesheets = sorted([(n, style_graph.degree(n)) for n in stylesheets], key=lambda x: x[1], reverse=True)[:20]
            
            nodes_to_keep = [n[0] for n in top_components] + [n[0] for n in top_stylesheets]
            style_graph = style_graph.subgraph(nodes_to_keep)
        
        # Position nodes using bipartite layout
        pos = nx.spring_layout(style_graph, seed=42, k=0.7)
        
        # Determine node colors based on type
        node_colors = []
        for node in style_graph.nodes():
            if node in components:
                node_colors.append('skyblue')
            else:
                node_colors.append('lightgreen')
                
        # Draw the graph
        nx.draw(
            style_graph,
            pos,
            with_labels=True,
            node_color=node_colors,
            node_size=800,
            font_size=8,
            alpha=0.8,
            edge_color='gray'
        )
        
        # Add a legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='skyblue', markersize=10, label='Component'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgreen', markersize=10, label='Stylesheet')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        plt.title(f'Stylesheet Relationship Graph ({len(components)} components, {len(stylesheets)} stylesheets)')
        plt.savefig(self.output_dir / 'style_graph.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _generate_dependency_graph(self) -> None:
        """Generate dependency graph visualization and report."""
        print("Generating dependency graph...")
        
        # Skip if the graph is empty
        if self.dependency_graph.number_of_edges() == 0:
            return
            
        plt.figure(figsize=(14, 12))
        
        # Limit graph size for readability
        if self.dependency_graph.number_of_nodes() > 50:
            # Find important nodes (hubs and authorities)
            hub_scores = nx.hits(self.dependency_graph)[0]
            auth_scores = nx.hits(self.dependency_graph)[1]
            
            # Combine scores and keep top nodes
            combined_scores = {node: hub_scores.get(node, 0) + auth_scores.get(node, 0) 
                              for node in self.dependency_graph.nodes()}
            
            top_nodes = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:50]
            sub_graph = self.dependency_graph.subgraph([n[0] for n in top_nodes])
        else:
            sub_graph = self.dependency_graph
        
        # Calculate node importance metrics
        in_degrees = dict(sub_graph.in_degree())
        out_degrees = dict(sub_graph.out_degree())
        
        # Create node sizes based on degree
        node_sizes = [300 + (in_degrees.get(node, 0) + out_degrees.get(node, 0)) * 50 for node in sub_graph.nodes()]
        
        # Color nodes based on type if available
        node_colors = []
        for node in sub_graph.nodes():
            if node in self.analysis_results:
                component_name = self.analysis_results[node].component_name
                if component_name in self.component_map:
                    if self.component_map[component_name].type == 'functional':
                        node_colors.append('skyblue')
                    elif self.component_map[component_name].type == 'class':
                        node_colors.append('salmon')
                    elif self.component_map[component_name].type == 'hook':
                        node_colors.append('lightgreen')
                    elif self.component_map[component_name].type == 'context':
                        node_colors.append('purple')
                    else:
                        node_colors.append('lightgray')
                else:
                    node_colors.append('lightgray')
            else:
                node_colors.append('lightgray')
        
        # Set node labels to component names instead of file paths
        labels = {}
        for node in sub_graph.nodes():
            if node in self.analysis_results:
                labels[node] = self.analysis_results[node].component_name
            else:
                # Extract just the filename for display
                labels[node] = Path(node).name
        
        # Use a spring layout
        pos = nx.spring_layout(sub_graph, seed=42, k=0.6)
        
        # Draw the graph
        nx.draw(
            sub_graph,
            pos,
            labels=labels,
            node_color=node_colors,
            node_size=node_sizes,
            font_size=8,
            arrows=True,
            alpha=0.8,
            edge_color='gray',
            width=0.7
        )
        
        # Add a legend for node types
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='skyblue', markersize=10, label='Functional'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='salmon', markersize=10, label='Class'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgreen', markersize=10, label='Hook'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='purple', markersize=10, label='Context'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgray', markersize=10, label='Other')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        plt.title(f'Dependency Graph ({sub_graph.number_of_nodes()} components, {sub_graph.number_of_edges()} dependencies)')
        plt.savefig(self.output_dir / 'dependency_graph.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Generate dependency metrics report
        self._generate_dependency_metrics(sub_graph)

    def _generate_dependency_metrics(self, graph: nx.DiGraph) -> None:
        """Generate dependency metrics report."""
        metrics_path = self.output_dir / 'dependency_metrics.md'
        
        try:
            # Calculate various metrics
            in_degrees = dict(graph.in_degree())
            out_degrees = dict(graph.out_degree())
            
            # Identify potential bottleneck components
            highly_imported = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
            high_importers = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Calculate network metrics
            try:
                # These can fail if the graph is not connected or has other issues
                avg_shortest_path = nx.average_shortest_path_length(graph)
                diameter = nx.diameter(graph)
                density = nx.density(graph)
            except Exception:
                avg_shortest_path = "N/A (disconnected graph)"
                diameter = "N/A (disconnected graph)"
                density = nx.density(graph)
            
            # Identify potential circular dependencies
            cycles = list(nx.simple_cycles(graph))
            
            with open(metrics_path, 'w', encoding='utf-8') as f:
                f.write("# Dependency Analysis Metrics\n\n")
                
                f.write("## Graph Statistics\n\n")
                f.write(f"- **Number of Components**: {graph.number_of_nodes()}\n")
                f.write(f"- **Number of Dependencies**: {graph.number_of_edges()}\n")
                f.write(f"- **Graph Density**: {density:.4f}\n")
                f.write(f"- **Average Shortest Path Length**: {avg_shortest_path}\n")
                f.write(f"- **Graph Diameter**: {diameter}\n\n")
                
                f.write("## Most Imported Components\n\n")
                f.write("These components are imported by many others and could be bottlenecks or critical dependencies:\n\n")
                f.write("| Component | Imported By |\n")
                f.write("|-----------|------------|\n")
                for comp, count in highly_imported:
                    comp_name = self.analysis_results[comp].component_name if comp in self.analysis_results else Path(comp).name
                    f.write(f"| {comp_name} | {count} |\n")
                f.write("\n")
                
                f.write("## Components with Most Dependencies\n\n")
                f.write("These components import many others and might be too complex:\n\n")
                f.write("| Component | Number of Imports |\n")
                f.write("|-----------|------------------|\n")
                for comp, count in high_importers:
                    comp_name = self.analysis_results[comp].component_name if comp in self.analysis_results else Path(comp).name
                    f.write(f"| {comp_name} | {count} |\n")
                f.write("\n")
                
                if cycles:
                    f.write("## Circular Dependencies\n\n")
                    f.write("The following circular dependencies were detected:\n\n")
                    for i, cycle in enumerate(cycles[:10], 1):  # Limit to first 10 cycles
                        f.write(f"### Cycle {i}\n\n")
                        cycle_str = " → ".join([self.analysis_results[node].component_name 
                                              if node in self.analysis_results else Path(node).name
                                              for node in cycle])
                        f.write(f"{cycle_str} → (back to start)\n\n")
                    
                    if len(cycles) > 10:
                        f.write(f"*{len(cycles) - 10} additional cycles omitted for brevity*\n\n")
                else:
                    f.write("## Circular Dependencies\n\n")
                    f.write("No circular dependencies detected. Good job!\n\n")
                
                f.write("## Recommendations\n\n")
                
                if any(count > 5 for _, count in highly_imported):
                    f.write("- Consider breaking down heavily imported components into smaller, more focused utilities.\n")
                
                if any(count > 10 for _, count in high_importers):
                    f.write("- Components with many dependencies may be too complex. Consider refactoring them.\n")
                
                if cycles:
                    f.write("- Resolve circular dependencies to improve maintainability and reduce potential bugs.\n")
                
                if density > 0.3:
                    f.write("- High graph density indicates tight coupling. Consider introducing more abstraction layers.\n")
                
                f.write("\n*This report was generated automatically and may require human review.*\n")
                
            print(f"Dependency metrics report saved to {metrics_path}")
            
        except Exception as e:
            print(f"Error generating dependency metrics: {str(e)}")

    def _generate_optimization_report(self) -> None:
        """Generate path optimization suggestions report."""
        print("Generating optimization report...")
        
        output_path = self.output_dir / 'path_optimization.md'
        deep_imports = []
        large_components = []
        weak_typing = []
        refactoring_candidates = []
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Path Optimization Suggestions\n\n")
            
            # Check for deep relative imports
            for file_path, analysis in self.analysis_results.items():
                file_deep_imports = []
                
                for imp in analysis.imports:
                    if imp.is_relative and imp.source.count('../') > 2:
                        file_deep_imports.append({
                            'import': imp.source,
                            'suggestion': f'Consider using absolute import for improved readability'
                        })
                
                if file_deep_imports:
                    deep_imports.append({
                        'file': file_path,
                        'imports': file_deep_imports
                    })
            
            # Check for large components (by content size or number of render elements)
            for file_path, analysis in self.analysis_results.items():
                content_size = len(analysis.content)
                
                # Count JSX elements as a heuristic for component complexity
                jsx_elements = len(re.findall(r'<[A-Za-z][A-Za-z0-9_]*', analysis.content))
                
                if content_size > 1000 and jsx_elements > 20:
                    large_components.append({
                        'file': file_path,
                        'component': analysis.component_name,
                        'size': content_size,
                        'jsx_elements': jsx_elements,
                        'suggestion': 'Consider breaking into smaller components for maintainability'
                    })
            
            # Identify components that might benefit from prop-types or TypeScript
            for file_path, analysis in self.analysis_results.items():
                for component in analysis.components:
                    if component.type == 'functional' and len(component.props) > 3:
                        if not re.search(r'PropTypes|: React\.FC<|interface Props', analysis.content):
                            weak_typing.append({
                                'file': file_path,
                                'component': component.name,
                                'props_count': len(component.props),
                                'suggestion': 'Consider adding PropTypes or TypeScript interfaces'
                            })
            
            # Identify refactoring candidates (components with many imports and render elements)
            for file_path, analysis in self.analysis_results.items():
                if len(analysis.imports) > 10 and len(re.findall(r'<[A-Za-z][A-Za-z0-9_]*', analysis.content)) > 15:
                    refactoring_candidates.append({
                        'file': file_path,
                        'component': analysis.component_name,
                        'imports_count': len(analysis.imports),
                        'suggestion': 'Consider refactoring into smaller, more focused components'
                    })
            
            # Write deep imports section
            if deep_imports:
                f.write("## Deep Relative Imports\n\n")
                f.write("The following files use deep relative imports that could be simplified:\n\n")
                
                for entry in deep_imports:
                    f.write(f"### {entry['file']}\n\n")
                    for imp in entry['imports']:
                        f.write(f"- `{imp['import']}` - {imp['suggestion']}\n")
                    f.write("\n")
            
            # Write large components section
            if large_components:
                f.write("## Large Components\n\n")
                f.write("These components are unusually large and might benefit from being split:\n\n")
                f.write("| Component | File | Size (chars) | JSX Elements | Suggestion |\n")
                f.write("|-----------|------|--------------|--------------|------------|\n")
                
                for comp in large_components:
                    f.write(f"| {comp['component']} | {comp['file']} | {comp['size']} | {comp['jsx_elements']} | {comp['suggestion']} |\n")
                f.write("\n")
            
            # Write weak typing section
            if weak_typing:
                f.write("## Components Lacking Type Definitions\n\n")
                f.write("These components have multiple props but lack PropTypes or TypeScript interfaces:\n\n")
                f.write("| Component | File | Props Count | Suggestion |\n")
                f.write("|-----------|------|-------------|------------|\n")
                
                for comp in weak_typing:
                    f.write(f"| {comp['component']} | {comp['file']} | {comp['props_count']} | {comp['suggestion']} |\n")
                f.write("\n")
            
            # Write refactoring candidates section
            if refactoring_candidates:
                f.write("## Refactoring Candidates\n\n")
                f.write("These components have high complexity and many dependencies:\n\n")
                f.write("| Component | File | Import Count | Suggestion |\n")
                f.write("|-----------|------|--------------|------------|\n")
                
                for comp in refactoring_candidates:
                    f.write(f"| {comp['component']} | {comp['file']} | {comp['imports_count']} | {comp['suggestion']} |\n")
                f.write("\n")
            
            # If no issues were found
            if not (deep_imports or large_components or weak_typing or refactoring_candidates):
                f.write("No significant optimization issues detected. Great job!\n")
            
            f.write("\n## General Recommendations\n\n")
            f.write("1. Consider using absolute imports for better code organization\n")
            f.write("2. Break large components into smaller, more focused ones\n")
            f.write("3. Use TypeScript or PropTypes to improve type safety\n")
            f.write("4. Keep the dependency graph as acyclic as possible\n")
            f.write("5. Group related functionality into cohesive modules\n")

    def _generate_state_flow_diagram(self) -> None:
        """Generate state flow diagram and analysis report."""
        print("Generating state flow diagram...")
        
        # Skip if no data for state flow
        if len(self.state_flow_graph) < 2:
            return
            
        plt.figure(figsize=(14, 12))
        
        # Limit graph size for readability
        if len(self.state_flow_graph) > 40:
            # Keep only the most connected components
            top_nodes = sorted(self.state_flow_graph.degree, key=lambda x: x[1], reverse=True)[:40]
            sub_graph = self.state_flow_graph.subgraph([n[0] for n in top_nodes])
        else:
            sub_graph = self.state_flow_graph
        
        # Use edge colors to distinguish prop drilling vs context
        edge_colors = []
        for u, v, data in sub_graph.edges(data=True):
            if data.get('type') == 'context':
                edge_colors.append('green')
            else:
                edge_colors.append('red')
        
        # Node colors based on component type
        node_colors = []
        for node in sub_graph.nodes():
            if node in self.component_map:
                if self.component_map[node].type == 'context':
                    node_colors.append('purple')
                elif self.component_map[node].type == 'hook':
                    node_colors.append('lightgreen')
                elif any(h.hook_name == 'useState' for h in self.component_map[node].hooks):
                    node_colors.append('orange')
                else:
                    node_colors.append('skyblue')
            else:
                node_colors.append('lightgray')
        
        # Use a spring layout
        pos = nx.spring_layout(sub_graph, seed=42, k=0.6)
        
        # Draw the graph
        nx.draw(
            sub_graph,
            pos,
            with_labels=True,
            node_color=node_colors,
            edge_color=edge_colors,
            node_size=800,
            font_size=8,
            arrows=True,
            alpha=0.8,
            width=1.0
        )
        
        # Add a legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='purple', markersize=10, label='Context Provider'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgreen', markersize=10, label='Custom Hook'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=10, label='Stateful Component'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='skyblue', markersize=10, label='Regular Component'),
            plt.Line2D([0], [0], color='green', lw=2, label='Context Propagation'),
            plt.Line2D([0], [0], color='red', lw=2, label='Prop Drilling')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        plt.title(f'State Flow Diagram ({sub_graph.number_of_nodes()} components)')
        plt.savefig(self.output_dir / 'state_flow_diagram.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Generate state flow analysis report
        self._generate_state_flow_analysis(sub_graph)

    def _generate_state_flow_analysis(self, graph: nx.DiGraph) -> None:
        """Generate state flow analysis report."""
        flow_path = self.output_dir / 'state_flow_analysis.md'
        
        try:
            # Count prop drilling levels
            max_prop_drilling = 0
            prop_drilling_chains = []
            
            # Find paths in the graph that represent prop drilling
            for source in graph.nodes():
                for target in graph.nodes():
                    if source != target:
                        try:
                            # Find all simple paths between these nodes
                            for path in nx.all_simple_paths(graph, source, target, cutoff=5):
                                if len(path) > 2:  # Only consider paths with at least 2 edges
                                    # Check if this is a prop drilling path (all 'props' type edges)
                                    is_prop_drilling = True
                                    for i in range(len(path) - 1):
                                        edge_data = graph.get_edge_data(path[i], path[i+1])
                                        if edge_data and edge_data.get('type') != 'props':
                                            is_prop_drilling = False
                                            break
                                    
                                    if is_prop_drilling:
                                        max_prop_drilling = max(max_prop_drilling, len(path) - 1)
                                        if len(path) - 1 >= 3:  # Only report chains of length 3+
                                            prop_drilling_chains.append({
                                                'source': source,
                                                'target': target,
                                                'path': path,
                                                'length': len(path) - 1
                                            })
                        except nx.NetworkXNoPath:
                            pass
            
            # Find context providers and consumers
            context_providers = [node for node in graph.nodes() 
                            if node in self.component_map and self.component_map[node].type == 'context']
            
            context_consumers = set()
            for u, v, data in graph.edges(data=True):
                if data.get('type') == 'context':
                    context_consumers.add(v)
            
            # Find stateful components (with useState)
            stateful_components = [node for node in graph.nodes() 
                                if node in self.component_map and 
                                any(h.hook_name == 'useState' for h in self.component_map[node].hooks)]
            
            # Write the report
            with open(flow_path, 'w', encoding='utf-8') as f:
                f.write("# State Flow Analysis\n\n")
                
                f.write("## Overview\n\n")
                f.write(f"- **Total Components**: {graph.number_of_nodes()}\n")
                f.write(f"- **Context Providers**: {len(context_providers)}\n")
                f.write(f"- **Context Consumers**: {len(context_consumers)}\n")
                f.write(f"- **Stateful Components**: {len(stateful_components)}\n")
                f.write(f"- **Maximum Prop Drilling Depth**: {max_prop_drilling}\n\n")
                
                # Context usage section
                if context_providers:
                    f.write("## Context Usage\n\n")
                    for provider in context_providers:
                        f.write(f"### {provider}\n\n")
                        consumers = [v for u, v, data in graph.edges(data=True) 
                                if u == provider and data.get('type') == 'context']
                        
                        if consumers:
                            f.write("**Direct Consumers:**\n\n")
                            for consumer in consumers:
                                f.write(f"- {consumer}\n")
                        else:
                            f.write("*No direct consumers identified*\n")
                        f.write("\n")
                
                # Prop drilling section
                if prop_drilling_chains:
                    f.write("## Prop Drilling Chains\n\n")
                    f.write("The following chains represent potential prop drilling patterns:\n\n")
                    
                    # Sort chains by length (longest first)
                    sorted_chains = sorted(prop_drilling_chains, key=lambda x: x['length'], reverse=True)
                    
                    for i, chain in enumerate(sorted_chains[:10], 1):  # Limit to 10 chains
                        f.write(f"### Chain {i} (Depth: {chain['length']})\n\n")
                        path_str = " → ".join(chain['path'])
                        f.write(f"{path_str}\n\n")
                    
                    if len(sorted_chains) > 10:
                        f.write(f"*{len(sorted_chains) - 10} additional chains omitted for brevity*\n\n")
                
                # Stateful components section
                if stateful_components:
                    f.write("## Stateful Components\n\n")
                    f.write("The following components manage local state:\n\n")
                    
                    for component in stateful_components:
                        if component in self.component_map:
                            state_vars = [h.state_variable for h in self.component_map[component].hooks 
                                    if h.hook_name == 'useState' and h.state_variable]
                            if state_vars:
                                f.write(f"- **{component}**: {', '.join(state_vars)}\n")
                            else:
                                f.write(f"- **{component}**\n")
                    f.write("\n")
                
                # Recommendations section
                f.write("## Recommendations\n\n")
                
                if max_prop_drilling > 3:
                    f.write("- **Reduce Prop Drilling**: Consider using Context API or state management libraries for deeply nested prop chains.\n")
                
                if len(stateful_components) > len(graph.nodes()) * 0.5:
                    f.write("- **Consolidate State Management**: A high proportion of components have local state. Consider using a more centralized approach.\n")
                
                if not context_providers and graph.number_of_nodes() > 10:
                    f.write("- **Add Context**: For a project of this size, Context API could simplify state management.\n")
                
                if context_providers and len(context_consumers) < 3:
                    f.write("- **Expand Context Usage**: Context providers exist but are underutilized.\n")
                
                f.write("\n*This report was generated automatically and may require human review.*\n")
            
            print(f"State flow analysis report saved to {flow_path}")
            
        except Exception as e:
            print(f"Error generating state flow analysis: {str(e)}")

def main():
    """Main execution function"""
    config = AnalysisConfig.create_default()
    analyzer = EnhancedProjectAnalyzer(config)
    analyzer.analyze_project()

if __name__ == "__main__":
    main()
