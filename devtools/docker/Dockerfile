FROM molssi/mamba141

COPY ./packmol_step/data/seamm-packmol.yml /root/environment.yml

RUN mamba env update -f /root/environment.yml

WORKDIR /home
ENTRYPOINT ["packmol"]
