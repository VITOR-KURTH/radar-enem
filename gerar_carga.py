# monitoramento_integrado.py
import subprocess
import json
import requests
import time
from datetime import datetime
import threading
import os
import re

class MonitoramentoIntegrado:
    def __init__(self, container="radar-enem", arquivo_stats="stats.json", 
                 arquivo_reqs="requisicoes.json"):
        self.container = container
        self.arquivo_stats = arquivo_stats
        self.arquivo_reqs = arquivo_reqs
        self.stats = []
        self.requisicoes = []
        self.rodando = True
        self.total_requisicoes = 0
        
    def capturar_stats(self):
        """Thread para capturar stats periodicamente - Versao robusta"""
        while self.rodando:
            try:
                # COMANDO MAIS SIMPLES E CONFAVEL
                cmd = f"docker stats {self.container} --no-stream"
                resultado = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
                
                # Processa a saida manualmente
                lines = resultado.strip().split('\n')
                if len(lines) >= 2:
                    # Pega a segunda linha (primeira linha e cabecalho)
                    data_line = lines[1]
                    
                    # Remove espacos extras e divide
                    parts = re.split(r'\s{2,}', data_line.strip())
                    
                    # Mapeia os campos
                    if len(parts) >= 8:
                        # Remove caracteres especiais
                        container = parts[0].replace('/', '').strip()
                        cpu = parts[1].strip()
                        mem_usage = parts[2].strip()
                        mem_perc = parts[3].strip()
                        net_io = parts[4].strip()
                        block_io = parts[5].strip()
                        pids = parts[6].strip()
                        
                        # Cria objeto stats
                        stats = {
                            'Container': container,
                            'CPUPerc': cpu,
                            'MemUsage': mem_usage,
                            'MemPerc': mem_perc,
                            'NetIO': net_io,
                            'BlockIO': block_io,
                            'PIDs': pids,
                            'timestamp': datetime.now().isoformat(),
                            'timestamp_ms': int(time.time() * 1000)
                        }
                        
                        self.stats.append(stats)
                        
                        # Salva no arquivo
                        with open(self.arquivo_stats, 'a') as f:
                            f.write(json.dumps(stats) + '\n')
                        
                        # Debug (opcional)
                        # print(f"[Stats] CPU: {cpu}, Mem: {mem_usage}")
                
                time.sleep(2)
                
            except subprocess.CalledProcessError as e:
                print(f"Erro no docker stats: {e}")
                time.sleep(1)
            except Exception as e:
                print(f"Erro no captura_stats: {e}")
                time.sleep(1)
    
    def fazer_requisicao(self, url="http://localhost:5000/nota/650"):
        """Faz uma requisicao e registra"""
        inicio = time.time()
        timestamp = int(inicio * 1000)
        
        try:
            response = requests.get(url, timeout=2)
            tempo = int((time.time() - inicio) * 1000)
            
            req = {
                'numero': self.total_requisicoes + 1,
                'status': response.status_code,
                'tempo_ms': tempo,
                'timestamp': datetime.now().isoformat(),
                'timestamp_ms': timestamp,
                'sucesso': response.status_code == 200
            }
        except Exception as e:
            req = {
                'numero': self.total_requisicoes + 1,
                'status': 'ERROR',
                'tempo_ms': int((time.time() - inicio) * 1000),
                'timestamp': datetime.now().isoformat(),
                'timestamp_ms': timestamp,
                'sucesso': False,
                'erro': str(e)
            }
        
        self.total_requisicoes += 1
        self.requisicoes.append(req)
        
        # Salva no arquivo
        with open(self.arquivo_reqs, 'a') as f:
            f.write(json.dumps(req) + '\n')
        
        return req
    
    def executar_carga(self, total_requisicoes=100, delay=0.1):
        """Executa a carga de requisicoes"""
        print(f"INICIANDO CARGA DE {total_requisicoes} REQUISICOES")
        print(f"DELAY ENTRE REQUISICOES: {delay}s")
        print("=" * 60)
        
        for i in range(total_requisicoes):
            req = self.fazer_requisicao()
            
            if req['sucesso']:
                status_icon = "[OK]"
            else:
                status_icon = "[ERRO]"
            
            print(f"{status_icon} Req {req['numero']:4d} | Status: {req['status']:>5} | {req['tempo_ms']:>4}ms")
            
            time.sleep(delay)
        
        print("=" * 60)
        print("CARGA FINALIZADA!")
    
    def executar(self, total_requisicoes=100, intervalo_stats=2, delay_requisicoes=0.1):
        """Executa monitoramento completo"""
        
        # Limpa arquivos antigos
        for arquivo in [self.arquivo_stats, self.arquivo_reqs]:
            with open(arquivo, 'w') as f:
                f.write('')
        
        # Inicia thread para capturar stats
        thread_stats = threading.Thread(target=self.capturar_stats)
        thread_stats.daemon = True
        thread_stats.start()
        
        print("=" * 60)
        print("MONITORAMENTO INTEGRADO INICIADO")
        print("=" * 60)
        print(f"Stats: {self.arquivo_stats}")
        print(f"Requisicoes: {self.arquivo_reqs}")
        print(f"Intervalo stats: {intervalo_stats}s")
        print(f"Total requisicoes: {total_requisicoes}")
        print("=" * 60)
        
        # Aguarda primeira captura
        time.sleep(1)
        
        # Executa carga
        self.executar_carga(total_requisicoes, delay_requisicoes)
        
        # Para a captura
        self.rodando = False
        thread_stats.join(timeout=5)
        
        # Gera relatorio
        self.gerar_relatorio_final()
    
    def gerar_relatorio_final(self):
        """Gera relatorio completo"""
        print("\n" + "=" * 60)
        print("RELATORIO FINAL")
        print("=" * 60)
        
        # Estatisticas de requisicoes
        total = len(self.requisicoes)
        sucessos = sum(1 for r in self.requisicoes if r['sucesso'])
        erros = total - sucessos
        tempos = [r['tempo_ms'] for r in self.requisicoes if r['tempo_ms'] > 0]
        
        print(f"\nREQUISICOES:")
        print(f"   Total: {total}")
        print(f"   Sucessos: {sucessos} ({sucessos/total*100:.1f}%)")
        print(f"   Erros: {erros} ({erros/total*100:.1f}%)")
        if tempos:
            print(f"   Tempo medio: {sum(tempos)/len(tempos):.2f}ms")
            print(f"   Tempo minimo: {min(tempos):.2f}ms")
            print(f"   Tempo maximo: {max(tempos):.2f}ms")
        
        # Estatisticas de CPU
        cpus = []
        for s in self.stats:
            try:
                cpu = float(s['CPUPerc'].replace('%', ''))
                cpus.append(cpu)
            except:
                continue
        
        if cpus:
            print(f"\nCPU:")
            print(f"   Minimo: {min(cpus):.2f}%")
            print(f"   Maximo: {max(cpus):.2f}%")
            print(f"   Media: {sum(cpus)/len(cpus):.2f}%")
        
        # Estatisticas de Memoria
        mems = []
        for s in self.stats:
            try:
                mem_usage = s['MemUsage']
                # Extrai apenas o numero antes do primeiro espaco
                parts = mem_usage.split()
                if len(parts) >= 1:
                    mem_num = float(parts[0])
                    # Verifica se a unidade e GB
                    if len(parts) >= 2 and 'G' in parts[1]:
                        mem_num = mem_num * 1024
                    mems.append(mem_num)
            except:
                continue
        
        if mems:
            print(f"\nMEMORIA:")
            print(f"   Minimo: {min(mems):.2f} MB")
            print(f"   Maximo: {max(mems):.2f} MB")
            print(f"   Media: {sum(mems)/len(mems):.2f} MB")
        
        print("\n" + "=" * 60)
        print("Dados salvos em:")
        print(f"   Stats: {self.arquivo_stats}")
        print(f"   Requisicoes: {self.arquivo_reqs}")
        
        # Mostra quantas capturas foram salvas
        print(f"\nTotal de capturas de stats: {len(self.stats)}")

# Executa
if __name__ == "__main__":
    monitor = MonitoramentoIntegrado()
    monitor.executar(
        total_requisicoes=100,
        intervalo_stats=2,
        delay_requisicoes=0.1
    )
