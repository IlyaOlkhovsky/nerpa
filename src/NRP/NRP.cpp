#include <fstream>
#include <iostream>
#include <sstream>
#include <algorithm>
#include "NRP.h"

std::string nrp::NRP::getFormula(int i) const {
    return strformula[i];
}

std::string nrp::NRP::getGraphInString() const {
    return graph;
}

int nrp::NRP::getLen() const {
    return aminoacids.size();
}

int nrp::NRP::getInd(int i) const {
    return position[i];
}

aminoacid::Aminoacids::Aminoacid nrp::NRP::getAminoacid(int i) const {
    return aminoacids[i];
}

void nrp::NRP::print() const {
    for (int i = 0; i < (int)aminoacids.size(); ++i) {
        std::cerr << aminoacid::Aminoacids::AMINOACID_NAMES[aminoacids[i]] << "(" << position[i] << ") ";
    }
    std::cerr << "\n";
}


std::string nrp::NRP::get_file_name() const {
    return file_name;
}

std::string nrp::NRP::get_extra_info() const {
    return extra_info;
}

std::vector<aminoacid::Aminoacids::Aminoacid> nrp::NRP::getAminoacids() const {
    return aminoacids;
}
