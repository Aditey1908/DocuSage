import re
from collections import Counter
from typing import List, Tuple, Dict, Set

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Remove repeated headers/footers by frequency analysis
    lines = text.split('\n')
    line_counts = Counter(line.strip() for line in lines if line.strip())
    
    # Remove lines that appear frequently (likely headers/footers)
    threshold = max(2, len(lines) * 0.05)  # Lines appearing in >5% of document
    boilerplate = {line for line, count in line_counts.items() if count > threshold and len(line) > 10}
    
    cleaned_lines = []
    for line in lines:
        if line.strip() not in boilerplate:
            cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # Normalize whitespace but preserve structure
    text = re.sub(r'[ \t]+\n', '\n', text)  # Remove trailing spaces
    text = re.sub(r'\n{4,}', '\n\n\n', text)  # Limit excessive blank lines to max 3
    
    # Standardize bullets while preserving indentation
    lines = text.split('\n')
    for i, line in enumerate(lines):
        # Only modify bullet patterns, preserve indentation
        if line.strip():
            indent = len(line) - len(line.lstrip())
            content = line.lstrip()
            # Standardize bullets
            content = re.sub(r'^[•—–*]\s*', '- ', content)
            lines[i] = ' ' * indent + content
    
    return '\n'.join(lines)

def get_indentation_level(line: str) -> int:
    """Get the indentation level of a line."""
    return len(line) - len(line.lstrip())

def extract_list_marker(line: str) -> Tuple[str, str]:
    """Extract list marker and remaining text."""
    stripped = line.lstrip()
    
    # Check for numbered lists (1., 2., 1.1., etc.)
    match = re.match(r'^(\d+(?:\.\d+)*\s*[\.\)]\s*)', stripped)
    if match:
        return match.group(1), stripped[len(match.group(1)):]
    
    # Check for roman numerals (i., ii., iii., etc.)
    match = re.match(r'^([ivxlcdm]+\s*[\.\)]\s*)', stripped, re.IGNORECASE)
    if match:
        return match.group(1), stripped[len(match.group(1)):]
    
    # Check for alphabetic (a., b., c., etc.)
    match = re.match(r'^([a-z]\s*[\.\)]\s*)', stripped, re.IGNORECASE)
    if match:
        return match.group(1), stripped[len(match.group(1)):]
    
    # Check for dash/bullet
    match = re.match(r'^(-\s+)', stripped)
    if match:
        return match.group(1), stripped[len(match.group(1)):]
    
    return "", stripped

def is_section_header(line: str) -> bool:
    """Detect section headers (ALL CAPS, short lines, etc.)."""
    stripped = line.strip()
    if not stripped:
        return False
    
    words = stripped.split()
    if len(words) <= 12 and not re.search(r'[.?!]$', stripped):
        caps_ratio = sum(1 for w in words if w.isupper()) / len(words) if words else 0
        title_ratio = sum(1 for w in words if w.istitle()) / len(words) if words else 0
        
        return caps_ratio >= 0.7 or title_ratio >= 0.7
    
    return False

def is_term_header(line: str, next_line_indent: int, current_indent: int) -> bool:
    """Detect if a line is a term header based on provided criteria."""
    words = line.strip().split()
    if len(words) <= 10 and not re.search(r'[.?!]', line):
        caps_ratio = sum(1 for w in words if w.isupper()) / len(words) if words else 0
        title_ratio = sum(1 for w in words if w.istitle()) / len(words) if words else 0
        
        if caps_ratio >= 0.7 or title_ratio >= 0.7:
            if next_line_indent > current_indent:
                return True
    
    return False

def is_table_line(line: str) -> bool:
    """Check if a line is part of a table (contains pipes)."""
    return '|' in line.strip()

class HierarchicalNode:
    """Represents a node in the hierarchical structure."""
    
    def __init__(self, content: str = "", indent: int = 0, marker: str = ""):
        self.content = content
        self.indent = indent
        self.marker = marker
        self.children: List['HierarchicalNode'] = []
        self.parent: 'HierarchicalNode' = None  # Fixed: removed extra ]
        self.is_section_header = False
        self.is_table = False
    
    def add_child(self, child: 'HierarchicalNode'):
        child.parent = self
        self.children.append(child)
    
    def get_full_text_with_structure(self) -> str:
        """Get the full text preserving indentation structure."""
        lines = []
        
        if self.content.strip():
            lines.append(self.content)
        
        for child in self.children:
            child_text = child.get_full_text_with_structure()
            if child_text.strip():
                lines.append(child_text)
        
        return '\n'.join(lines)
    
    def get_context_path(self) -> List[str]:
        """Get the hierarchical path to this node for context."""
        path = []
        current = self.parent
        
        while current and current.content.strip():
            if current.is_section_header:
                path.insert(0, current.content.strip())
            current = current.parent
        
        return path
    
    def count_tokens(self) -> int:
        """Count tokens (words) in this node and all children."""
        return len(self.get_full_text_with_structure().split())

def build_hierarchical_structure(text: str) -> HierarchicalNode:
    """Build hierarchical structure from text based on indentation."""
    lines = text.split('\n')
    root = HierarchicalNode()
    stack = [root]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if not line.strip():
            i += 1
            continue
        
        current_indent = get_indentation_level(line)
        marker, content = extract_list_marker(line)
        
        # Check if this is a section header
        is_header = is_section_header(line)
        
        # Check if this is a term header - get next line indent safely
        next_indent = 0
        if i + 1 < len(lines) and lines[i + 1].strip():  # Fixed: added strip check
            next_indent = get_indentation_level(lines[i + 1])
        
        # Handle table detection
        if is_table_line(line):
            # Collect all table lines
            table_lines = [line]
            i += 1
            while i < len(lines) and is_table_line(lines[i]):
                table_lines.append(lines[i])
                i += 1
            
            # Create table node
            table_content = '\n'.join(table_lines)
            table_node = HierarchicalNode(table_content, current_indent, "")
            table_node.is_table = True
            
            # Find appropriate parent
            while len(stack) > 1 and stack[-1].indent >= current_indent:
                stack.pop()
            
            stack[-1].add_child(table_node)
            continue
        
        # Create new node
        node = HierarchicalNode(line, current_indent, marker)
        node.is_section_header = is_header
        
        # Find appropriate parent based on indentation
        while len(stack) > 1 and stack[-1].indent >= current_indent:
            stack.pop()
        
        stack[-1].add_child(node)
        stack.append(node)
        
        # If this is a term header, collect its definition
        if is_term_header(line, next_indent, current_indent):
            definition_lines = []
            i += 1
            while i < len(lines) and get_indentation_level(lines[i]) > current_indent:
                definition_lines.append(lines[i])
                i += 1
            
            if definition_lines:
                definition_content = '\n'.join(definition_lines)
                def_node = HierarchicalNode(definition_content, next_indent, "")
                node.add_child(def_node)
            
            continue
        
        i += 1
    
    return root

def create_semantic_chunks(node: HierarchicalNode, max_tokens: int = 1350, overlap_tokens: int = 150) -> List[str]:
    """Create chunks that preserve hierarchical structure and context."""
    chunks = []
    
    def collect_chunkable_nodes(n: HierarchicalNode) -> List[HierarchicalNode]:
        nodes = []
        
        # If this node has substantial content, include it
        if n.content.strip() and len(n.content.split()) > 5:
            nodes.append(n)
        
        # Recursively collect from children
        for child in n.children:
            nodes.extend(collect_chunkable_nodes(child))
        
        return nodes
    
    all_nodes = collect_chunkable_nodes(node)
    
    if not all_nodes:
        return chunks
    
    current_chunk_lines = []
    current_tokens = 0
    chunk_num = 1
    
    i = 0
    while i < len(all_nodes):
        current_node = all_nodes[i]
        node_text = current_node.get_full_text_with_structure()
        node_tokens = len(node_text.split())
        
        # If this single node exceeds max_tokens, split it
        if node_tokens > max_tokens:
            if current_chunk_lines:
                # Finalize current chunk
                chunk_content = '\n'.join(current_chunk_lines)
                chunks.append(f"=== CHUNK {chunk_num} ===\n{chunk_content}")
                chunk_num += 1
                current_chunk_lines = []
                current_tokens = 0
            
            # Split the large node
            large_node_chunks = split_large_node(current_node, max_tokens, chunk_num)
            chunks.extend(large_node_chunks)
            chunk_num += len(large_node_chunks)
            i += 1
            continue
        
        # Check if adding this node would exceed the limit
        if current_tokens + node_tokens > max_tokens and current_chunk_lines:
            # Finalize current chunk
            chunk_content = '\n'.join(current_chunk_lines)
            chunks.append(f"=== CHUNK {chunk_num} ===\n{chunk_content}")
            chunk_num += 1
            
            # Start new chunk with context if overlap is needed
            if overlap_tokens > 0 and current_chunk_lines:
                overlap_content = get_overlap_content(current_chunk_lines, overlap_tokens)
                current_chunk_lines = [overlap_content] if overlap_content else []
                current_tokens = len(overlap_content.split()) if overlap_content else 0
            else:
                current_chunk_lines = []
                current_tokens = 0
        
        # Add context path for better understanding
        context_path = current_node.get_context_path()
        if context_path:
            context_header = ' > '.join(context_path)
            # Check if context is already in current chunk
            current_chunk_text = '\n'.join(current_chunk_lines)
            if context_header and len(context_header.split()) < 50 and context_header not in current_chunk_text:
                context_line = f"[Context: {context_header}]"
                current_chunk_lines.append(context_line)
                current_tokens += len(context_header.split()) + 2
        
        # Add the node content
        current_chunk_lines.append(node_text)
        current_tokens += node_tokens
        
        i += 1
    
    # Don't forget the last chunk
    if current_chunk_lines:
        chunk_content = '\n'.join(current_chunk_lines)
        chunks.append(f"=== CHUNK {chunk_num} ===\n{chunk_content}")
    
    return chunks

def split_large_node(node: HierarchicalNode, max_tokens: int, start_chunk_num: int) -> List[str]:
    """Split a large node while preserving structure."""
    content = node.get_full_text_with_structure()
    lines = content.split('\n')
    chunks = []
    
    current_lines = []
    current_tokens = 0
    chunk_num = start_chunk_num
    
    # Add context for large node splitting
    context_path = node.get_context_path()
    if context_path:
        context_header = ' > '.join(context_path)
        context_line = f"[Context: {context_header}]"
        current_lines.append(context_line)
        current_tokens += len(context_header.split()) + 2
    
    for line in lines:
        line_tokens = len(line.split())
        
        if current_tokens + line_tokens > max_tokens and current_lines:
            chunk_content = '\n'.join(current_lines)
            chunks.append(f"=== CHUNK {chunk_num} ===\n{chunk_content}")
            chunk_num += 1
            
            # Reset for next chunk, maintaining context
            current_lines = []
            current_tokens = 0
            if context_path:
                current_lines.append(context_line)
                current_tokens = len(context_header.split()) + 2
        
        current_lines.append(line)
        current_tokens += line_tokens
    
    if current_lines:
        chunk_content = '\n'.join(current_lines)
        chunks.append(f"=== CHUNK {chunk_num} ===\n{chunk_content}")
    
    return chunks

def get_overlap_content(lines: List[str], target_tokens: int) -> str:
    """Get overlap content from the end of current chunk."""
    if not lines:
        return ""
    
    # Take from the end, up to target_tokens
    all_text = '\n'.join(lines)
    words = all_text.split()
    
    if len(words) <= target_tokens:
        return all_text
    
    # Take last target_tokens words and try to break at sentence boundaries
    overlap_words = words[-target_tokens:]
    overlap_text = ' '.join(overlap_words)
    
    # Try to find a good breaking point
    sentences = re.split(r'[.!?]+', overlap_text)
    if len(sentences) > 1:
        # Return from the start of the last complete sentence
        return '. '.join(sentences[1:]) if len(sentences) > 2 else overlap_text
    
    return overlap_text

def hierarchical_chunk_file(input_txt_path: str, output_txt_path: str, max_tokens: int = 1350, overlap_tokens: int = 150):
    """Main function to hierarchically chunk a text file."""
    try:
        # Read input file
        with open(input_txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Step 1: Clean text while preserving structure
        cleaned_text = clean_text(text)
        
        # Step 2: Build hierarchical structure
        root_node = build_hierarchical_structure(cleaned_text)
        
        # Step 3: Create semantic chunks that preserve hierarchy
        chunks = create_semantic_chunks(root_node, max_tokens=max_tokens, overlap_tokens=overlap_tokens)
        
        # Step 4: Write output
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(chunks))
        
        print(f"Successfully created {len(chunks)} chunks from {input_txt_path}")
        print(f"Output written to {output_txt_path}")
        
        # Print some stats
        total_words = len(cleaned_text.split())
        avg_chunk_size = total_words / len(chunks) if chunks else 0
        print(f"Total words: {total_words}, Average chunk size: {avg_chunk_size:.0f} words")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_txt_path}' not found.")
    except Exception as e:
        print(f"Error processing file: {str(e)}")

# Main execution
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        max_tokens = int(sys.argv[3]) if len(sys.argv) > 3 else 1350
        overlap_tokens = int(sys.argv[4]) if len(sys.argv) > 4 else 150
    else:
        input_file = "output4.txt"  # Default input file
        output_file = "chunked_output4.txt"  # Default output file
        max_tokens = 1350
        overlap_tokens = 150
    
    hierarchical_chunk_file(input_file, output_file, max_tokens, overlap_tokens)
