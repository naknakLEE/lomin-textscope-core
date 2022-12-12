ARG VERSION_BEFORE

FROM docker.lomin.ai/ts-pp:${VERSION_BEFORE}

COPY ./pp/ /workspace/pp_server/
COPY ./lovit/ /workspace/