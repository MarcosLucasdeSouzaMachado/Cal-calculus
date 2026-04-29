import os
import re
from pathlib import Path

class MIPStoBasicBinary:
    """Converte instruções MIPS básicas para binário"""
    # Dicionário de registradores
    REGISTERS = {
        '$zero': 0, '$at': 1, '$v0': 2, '$v1': 3,
        '$a0': 4, '$a1': 5, '$a2': 6, '$a3': 7,
        '$t0': 8, '$t1': 9, '$t2': 10, '$t3': 11, '$t4': 12, '$t5': 13, '$t6': 14, '$t7': 15,
        '$s0': 16, '$s1': 17, '$s2': 18, '$s3': 19, '$s4': 20, '$s5': 21, '$s6': 22, '$s7': 23,
        '$t8': 24, '$t9': 25,
        '$k0': 26, '$k1': 27,
        '$gp': 28, '$sp': 29, '$fp': 30, '$ra': 31
    }
    # Opcodes para instruções R-type
    OPCODES_R = {
        'add': ('000000', '100000'),
        'sub': ('000000', '100010'),
        'and': ('000000', '100100'),
        'or': ('000000', '100101'),
        'xor': ('000000', '100110'),
        'slt': ('000000', '101010'),
        'mult': ('000000', '011000'),
        'div': ('000000', '011010'),
        'mfhi': ('000000', '010000'),
        'mflo': ('000000', '010010'),
        'sll': ('000000', '000000'),
        'srl': ('000000', '000010'),
        'sra': ('000000', '000011'),
    }
    # Opcodes para instruções I-type
    OPCODES_I = {
        'addi': '001000',
        'andi': '001100',
        'ori': '001101',
        'xori': '001110',
        'lw': '100011',
        'sw': '101011',
        'beq': '000100',
        'bne': '000101',
        'slti': '001010',
    }
    # Opcodes para instruções J-type
    OPCODES_J = {
        'j': '000010',
        'jal': '000011',
    }
    def get_register_number(self, reg):
        """Converte nome do registrador para número"""
        reg = reg.strip().lower()
        if reg in self.REGISTERS:
            return self.REGISTERS[reg]
        raise ValueError(f"Registrador inválido: {reg}")
    def parse_memory_operand(self, operand):
        """Parse operand como 'offset($register)'"""
        match = re.match(r'(-?\d+)\s*\(\s*(\$\w+)\s*\)', operand.strip())
        if match:
            offset = int(match.group(1)) & 0xFFFF
            register = self.get_register_number(match.group(2))
            return offset, register
        raise ValueError(f"Formato de memória inválido: {operand}")
    def instruction_to_binary(self, instruction):
        """Converte uma instrução MIPS para binário"""
        instruction = instruction.strip().upper()
        # Remover comentários
        if '#' in instruction:
            instruction = instruction[:instruction.index('#')].strip()
        if not instruction:
            return None
        parts = instruction.split()
        opcode = parts[0].lower()
        try:
            # Instruções R-type (add, sub, and, or, sll, srl, etc)
            if opcode in self.OPCODES_R:
                op, func = self.OPCODES_R[opcode]
                if opcode in ['sll', 'srl', 'sra']:
                    # Formato: SLL rt, rs, shamt
                    rt = self.get_register_number(parts[1].rstrip(','))
                    rs = self.get_register_number(parts[2].rstrip(','))
                    shamt = int(parts[3]) & 0x1F
                    rd = rt
                else:
                    # Formato: ADD rd, rs, rt
                    rd = self.get_register_number(parts[1].rstrip(','))
                    rs = self.get_register_number(parts[2].rstrip(','))
                    rt = self.get_register_number(parts[3].rstrip(','))
                    shamt = 0
                # Formato: opcode(6) rs(5) rt(5) rd(5) shamt(5) func(6)
                binary = f"{op}{rs:05b}{rt:05b}{rd:05b}{shamt:05b}{func}"
                return binary
            # Instruções I-type (addi, lw, sw, beq, etc)
            elif opcode in self.OPCODES_I:
                op = self.OPCODES_I[opcode]
                if opcode in ['lw', 'sw']:
                    # Formato: lw rt, offset($rs)
                    rt = self.get_register_number(parts[1].rstrip(','))
                    # Combinar o resto como operando de memória
                    memory_operand = ' '.join(parts[2:])
                    immediate, rs = self.parse_memory_operand(memory_operand)
                elif opcode in ['beq', 'bne']:
                    rs = self.get_register_number(parts[1].rstrip(','))
                    rt = self.get_register_number(parts[2].rstrip(','))
                    immediate = int(parts[3]) & 0xFFFF
                else:
                    rt = self.get_register_number(parts[1].rstrip(','))
                    rs = self.get_register_number(parts[2].rstrip(','))
                    immediate = int(parts[3]) & 0xFFFF
                # Formato: opcode(6) rs(5) rt(5) immediate(16)
                binary = f"{op}{rs:05b}{rt:05b}{immediate:016b}"
                return binary
            # Instruções J-type (j, jal)
            elif opcode in self.OPCODES_J:
                op = self.OPCODES_J[opcode]
                address = int(parts[1]) & 0x3FFFFFF
                
                # Formato: opcode(6) address(26)
                binary = f"{op}{address:026b}"
                return binary
            else:
                return None
        except (IndexError, ValueError) as e:
            return None
    def convert_file(self, input_file, output_file):
        """Converte um arquivo MIPS para binário"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    
                    # Ignorar linhas vazias e comentários
                    if not line or line.startswith('#'):
                        continue
                    
                    binary = self.instruction_to_binary(line)
                    
                    if binary:
                        f.write(f"{binary}\n")
            return True
        except Exception as e:
            print(f"Erro ao converter {input_file}: {e}")
            return False
def find_usb_drive():
    """Detecta automaticamente o pendrive (D:, E:, F:, etc)"""
    import sys
    # Em Windows, procurar por drives
    if sys.platform == 'win32':
        for drive_letter in range(ord('D'), ord('Z') + 1):
            drive = f"{chr(drive_letter)}:"
            if os.path.exists(drive):
                return drive
    else:
        # Em Linux/Mac, procurar em /media ou /mnt
        for mount_point in ['/media', '/mnt']:
            if os.path.exists(mount_point):
                for item in os.listdir(mount_point):
                    path = os.path.join(mount_point, item)
                    if os.path.isdir(path):
                        return path
    return None
def process_mips_files_from_usb(usb_path=None):
    """Processa todos os arquivos TESTE-*.txt no pendrive"""
    converter = MIPStoBasicBinary()
    # Se não especificar o caminho, detectar automaticamente
    if usb_path is None:
        usb_path = find_usb_drive()
        if usb_path is None:
            print("X Erro: Nenhum pendrive detectado!")
            print("Conecte o pendrive ou especifique o caminho manualmente.")
            return
    # Verificar se o caminho existe
    if not os.path.exists(usb_path):
        print(f"X Erro: O caminho '{usb_path}' não existe!")
        return
    print(f"Procurando arquivos em: {usb_path}")
    # Procurar por arquivos TESTE-*.txt
    pattern = re.compile(r'TESTE-(\d+)\.txt$', re.IGNORECASE)
    files = []
    for root, dirs, filenames in os.walk(usb_path):
        for file in filenames:
            match = pattern.match(file)
            if match:
                full_path = os.path.join(root, file)
                files.append((int(match.group(1)), full_path, file))
    # Ordenar por número
    files.sort()
    if not files:
        print("X Nenhum arquivo TESTE-*.txt encontrado no pendrive!")
        return
    print(f"V Encontrados {len(files)} arquivo(s)\n")
    successful = 0
    failed = 0
    for numero, input_path, input_filename in files:
        # Determinar o diretório do arquivo
        input_dir = os.path.dirname(input_path)
        # Formato: TESTE-XX-RESULTADO.txt (no mesmo diretório)
        output_filename = f"TESTE-{numero:02d}-RESULTADO.txt"
        output_path = os.path.join(input_dir, output_filename)
        print(f"Processando: {input_filename}")
        print(f"Entrada:  {input_path}")
        print(f"Saída:    {output_path}")
        try:
            if converter.convert_file(input_path, output_path):
                print(f"V Concluído com sucesso!")
                successful += 1
            else:
                print(f"X Erro ao processar!")
                failed += 1
        except Exception as e:
            print(f"X Erro: {e}")
            failed += 1
        print()
    # Resumo final
    #print("=" * 60)
    #print(f"RESUMO DA CONVERSÃO")
    #print(f"V Sucesso: {successful} arquivo(s)")
    #print(f"X Falha: {failed} arquivo(s)")
    #print("=" * 60)
if __name__ == "__main__":
    import sys
    # Se passar um argumento, usar como caminho do pendrive
    if len(sys.argv) > 1:
        usb_path = sys.argv[1]
        print(f"Usando caminho especificado: {usb_path}")
        process_mips_files_from_usb(usb_path)
    else:
        # Tentar detectar automaticamente
        process_mips_files_from_usb()